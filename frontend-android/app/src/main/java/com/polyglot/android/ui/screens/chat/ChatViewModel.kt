package com.polyglot.android.ui.screens.chat

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.polyglot.android.data.api.ConversationStarterItem
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
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonObject

data class ChatUiState(
    val threadId: Long? = null,
    val title: String? = null,
    val loadingMessages: Boolean = true,
    val messages: List<MessageDto> = emptyList(),
    val starters: List<ConversationStarterItem> = emptyList(),
    val sending: Boolean = false,
    val input: String = "",
    val expandedCorrections: Set<Long> = emptySet(),
)

class ChatViewModel(initialThreadId: Long?, initialTitle: String?) : ViewModel() {
    private val chat = ServiceLocator.chatRepository
    private val tokenStore = ServiceLocator.tokenStore

    private val _state = MutableStateFlow(ChatUiState(threadId = initialThreadId, title = initialTitle))
    val state: StateFlow<ChatUiState> = _state.asStateFlow()

    private val _errors = MutableSharedFlow<String>()
    val errors: SharedFlow<String> = _errors.asSharedFlow()

    private val _scrollToEnd = MutableSharedFlow<Unit>(extraBufferCapacity = 1)
    val scrollToEnd: SharedFlow<Unit> = _scrollToEnd.asSharedFlow()

    private var optimisticId: Long? = null

    init {
        viewModelScope.launch { loadInitial() }
    }

    private suspend fun loadInitial() {
        val token = tokenStore.get() ?: run {
            _state.update { it.copy(loadingMessages = false) }
            return
        }
        if (_state.value.threadId == null) {
            runCatching { chat.starters(token) }
                .onSuccess { list -> _state.update { it.copy(starters = list) } }
        }
        val tid = _state.value.threadId
        if (tid != null) {
            runCatching { chat.messages(token, tid) }
                .onSuccess { list ->
                    _state.update { it.copy(messages = list, loadingMessages = false) }
                    _scrollToEnd.tryEmit(Unit)
                }
                .onFailure {
                    _state.update { it.copy(loadingMessages = false) }
                    _errors.emit(it.userFacingMessage("Could not load messages"))
                }
        } else {
            _state.update { it.copy(loadingMessages = false) }
        }
    }

    fun onInputChange(value: String) = _state.update { it.copy(input = value) }

    fun toggleCorrection(messageId: Long) = _state.update {
        val s = it.expandedCorrections
        it.copy(expandedCorrections = if (messageId in s) s - messageId else s + messageId)
    }

    fun sendCurrent() {
        val text = _state.value.input.trim()
        if (text.isEmpty() || _state.value.sending) return
        _state.update { it.copy(input = "") }
        val tempId = -System.currentTimeMillis()
        optimisticId = tempId
        val optimistic = MessageDto(
            id = tempId,
            threadId = _state.value.threadId ?: 0L,
            role = "user",
            content = buildJsonObject {
                put("text", JsonPrimitive(text))
                put("correction_status", JsonPrimitive("pending"))
            },
            createdAt = "",
            metadata = null,
        )
        _state.update { it.copy(messages = it.messages + optimistic) }
        _scrollToEnd.tryEmit(Unit)
        viewModelScope.launch { postTurn(text = text, starterId = null) }
    }

    fun sendStarter(starterId: String) {
        if (_state.value.sending || _state.value.threadId != null) return
        viewModelScope.launch { postTurn(text = null, starterId = starterId) }
    }

    private suspend fun postTurn(text: String?, starterId: String?) {
        val token = tokenStore.get() ?: return
        _state.update { it.copy(sending = true) }
        val result = runCatching {
            if (starterId != null) chat.sendStarter(token, starterId)
            else chat.sendText(token, _state.value.threadId, text!!)
        }
        result.onSuccess { resp ->
            val opt = optimisticId
            optimisticId = null
            _state.update {
                val without = if (opt != null) it.messages.filter { m -> m.id != opt } else it.messages
                val newThreadId = it.threadId ?: resp.threadId
                it.copy(
                    threadId = newThreadId,
                    title = it.title ?: resp.threadId?.let { tid -> "Chat $tid" },
                    messages = without + resp.userMessage + resp.assistantMessage,
                    sending = false,
                )
            }
            _scrollToEnd.tryEmit(Unit)
        }.onFailure { err ->
            val opt = optimisticId
            optimisticId = null
            _state.update {
                val msgs = if (opt != null) it.messages.filter { m -> m.id != opt } else it.messages
                it.copy(messages = msgs, sending = false)
            }
            _errors.emit(err.userFacingMessage("Could not send message"))
        }
    }

    companion object {
        fun factory(threadId: Long?, title: String?): ViewModelProvider.Factory =
            object : ViewModelProvider.Factory {
                @Suppress("UNCHECKED_CAST")
                override fun <T : ViewModel> create(modelClass: Class<T>): T =
                    ChatViewModel(threadId, title) as T
            }
    }
}
