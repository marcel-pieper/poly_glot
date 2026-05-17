package com.polyglot.android.ui.screens.explain

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.polyglot.android.data.api.ExplainSeed
import com.polyglot.android.data.api.MessageDto
import com.polyglot.android.data.api.userFacingMessage
import com.polyglot.android.di.ServiceLocator
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonObject

data class ExplainUiState(
    val sourceThreadId: Long,
    val sourceMessageId: Long,
    val explainThreadId: Long? = null,
    val messages: List<MessageDto> = emptyList(),
    val loadingMessages: Boolean = false,
    val sending: Boolean = false,
    val question: String = "",
)

class ExplainViewModel(sourceThreadId: Long, sourceMessageId: Long) : ViewModel() {
    private val repo = ServiceLocator.explainRepository
    private val tokenStore = ServiceLocator.tokenStore

    private val _state = MutableStateFlow(
        ExplainUiState(sourceThreadId = sourceThreadId, sourceMessageId = sourceMessageId),
    )
    val state: StateFlow<ExplainUiState> = _state.asStateFlow()

    private val _errors = MutableSharedFlow<String>()
    val errors: SharedFlow<String> = _errors.asSharedFlow()

    fun onQuestionChange(v: String) = _state.update { it.copy(question = v) }

    fun ask() {
        val text = _state.value.question.trim()
        if (text.isEmpty() || _state.value.sending) return
        _state.update { it.copy(question = "", sending = true) }
        val optimisticId = -System.currentTimeMillis()
        val optimistic = MessageDto(
            id = optimisticId,
            threadId = _state.value.explainThreadId ?: 0L,
            role = "user",
            content = buildJsonObject { put("text", JsonPrimitive(text)) },
            createdAt = "",
            metadata = null,
        )
        _state.update { it.copy(messages = it.messages + optimistic) }

        viewModelScope.launch {
            val token = tokenStore.get() ?: run {
                _state.update { it.copy(sending = false) }
                return@launch
            }
            val seed = if (_state.value.explainThreadId == null) {
                ExplainSeed(
                    sourceThreadId = _state.value.sourceThreadId,
                    sourceMessageId = _state.value.sourceMessageId,
                )
            } else null
            runCatching {
                repo.send(
                    token = token,
                    text = text,
                    threadId = _state.value.explainThreadId,
                    seed = seed,
                )
            }.onSuccess { resp ->
                _state.update { st ->
                    val without = st.messages.filter { it.id != optimisticId }
                    st.copy(
                        sending = false,
                        explainThreadId = st.explainThreadId ?: resp.threadId,
                        messages = without + resp.userMessage + resp.assistantMessage,
                    )
                }
            }.onFailure { err ->
                _state.update {
                    it.copy(sending = false, messages = it.messages.filter { m -> m.id != optimisticId })
                }
                _errors.emit(err.userFacingMessage("Could not send explain message"))
            }
        }
    }

    companion object {
        fun factory(sourceThreadId: Long, sourceMessageId: Long): ViewModelProvider.Factory =
            object : ViewModelProvider.Factory {
                @Suppress("UNCHECKED_CAST")
                override fun <T : ViewModel> create(modelClass: Class<T>): T =
                    ExplainViewModel(sourceThreadId, sourceMessageId) as T
            }
    }
}
