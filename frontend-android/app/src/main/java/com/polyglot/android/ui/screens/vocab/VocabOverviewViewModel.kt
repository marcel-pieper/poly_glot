package com.polyglot.android.ui.screens.vocab

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.polyglot.android.data.api.VocabItemDto
import com.polyglot.android.data.api.userFacingMessage
import com.polyglot.android.di.ServiceLocator
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class VocabOverviewUiState(
    val loading: Boolean = true,
    val refreshing: Boolean = false,
    val items: List<VocabItemDto> = emptyList(),
    val dueCount: Int = 0,
    val error: String? = null,
)

class VocabOverviewViewModel : ViewModel() {
    private val vocab = ServiceLocator.vocabRepository
    private val tokenStore = ServiceLocator.tokenStore

    private val _state = MutableStateFlow(VocabOverviewUiState())
    val state: StateFlow<VocabOverviewUiState> = _state.asStateFlow()

    fun refresh() {
        viewModelScope.launch {
            val alreadyLoaded = !_state.value.loading && _state.value.items.isNotEmpty()
            _state.update {
                it.copy(
                    refreshing = alreadyLoaded,
                    loading = !alreadyLoaded,
                )
            }
            load()
            _state.update { it.copy(refreshing = false, loading = false) }
        }
    }

    private suspend fun load() {
        val token = tokenStore.get() ?: run {
            _state.update { it.copy(error = "Not authenticated") }
            return
        }
        runCatching { vocab.list(token) }
            .onSuccess { resp ->
                _state.update {
                    it.copy(
                        items = resp.items,
                        dueCount = resp.dueCount,
                        error = null,
                    )
                }
            }
            .onFailure { err ->
                _state.update {
                    it.copy(error = err.userFacingMessage("Could not load vocabulary"))
                }
            }
    }

    companion object {
        val Factory: ViewModelProvider.Factory = object : ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : ViewModel> create(modelClass: Class<T>): T =
                VocabOverviewViewModel() as T
        }
    }
}
