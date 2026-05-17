package com.polyglot.android.ui.screens.chat

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.polyglot.android.data.api.ThreadDto
import com.polyglot.android.di.ServiceLocator
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class ChatOverviewUiState(
    val loading: Boolean = true,
    val refreshing: Boolean = false,
    val threads: List<ThreadDto> = emptyList(),
    val deletingThreadId: Long? = null,
    val titlingThreadIds: Set<Long> = emptySet(),
)

class ChatOverviewViewModel : ViewModel() {
    private val chat = ServiceLocator.chatRepository
    private val tokenStore = ServiceLocator.tokenStore

    private val _state = MutableStateFlow(ChatOverviewUiState())
    val state: StateFlow<ChatOverviewUiState> = _state.asStateFlow()

    init {
        viewModelScope.launch {
            load(initial = true)
        }
    }

    fun refresh() {
        viewModelScope.launch {
            _state.update { it.copy(refreshing = true) }
            load(initial = false)
            _state.update { it.copy(refreshing = false) }
        }
    }

    private suspend fun load(initial: Boolean) {
        val token = tokenStore.get() ?: run {
            if (initial) _state.update { it.copy(loading = false) }
            return
        }
        runCatching { chat.threads(token) }
            .onSuccess { list ->
                _state.update { it.copy(threads = list, loading = false) }
                list.filter { it.title.isNullOrEmpty() }.forEach { generateTitleFor(it.id) }
            }
            .onFailure {
                _state.update { it.copy(loading = false) }
            }
    }

    private fun generateTitleFor(threadId: Long) {
        viewModelScope.launch {
            val token = tokenStore.get() ?: return@launch
            _state.update { it.copy(titlingThreadIds = it.titlingThreadIds + threadId) }
            val newTitle = chat.generateTitle(token, threadId)
            _state.update {
                it.copy(
                    titlingThreadIds = it.titlingThreadIds - threadId,
                    threads = it.threads.map { t -> if (t.id == threadId && newTitle != null) t.copy(title = newTitle) else t },
                )
            }
        }
    }

    fun delete(thread: ThreadDto) {
        viewModelScope.launch {
            val token = tokenStore.get() ?: return@launch
            _state.update { it.copy(deletingThreadId = thread.id) }
            runCatching { chat.delete(token, thread.id) }
                .onSuccess {
                    _state.update {
                        it.copy(
                            deletingThreadId = null,
                            threads = it.threads.filter { t -> t.id != thread.id },
                        )
                    }
                }
                .onFailure {
                    _state.update { it.copy(deletingThreadId = null) }
                }
        }
    }

    companion object {
        val Factory: ViewModelProvider.Factory = object : ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : ViewModel> create(modelClass: Class<T>): T = ChatOverviewViewModel() as T
        }
    }
}
