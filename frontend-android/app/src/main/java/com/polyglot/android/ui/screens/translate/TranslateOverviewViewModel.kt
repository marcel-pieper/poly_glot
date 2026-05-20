package com.polyglot.android.ui.screens.translate

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.polyglot.android.data.api.TranslationSummaryDto
import com.polyglot.android.di.ServiceLocator
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class TranslateOverviewUiState(
    val loading: Boolean = true,
    val refreshing: Boolean = false,
    val translations: List<TranslationSummaryDto> = emptyList(),
)

class TranslateOverviewViewModel : ViewModel() {
    private val translate = ServiceLocator.translateRepository
    private val tokenStore = ServiceLocator.tokenStore

    private val _state = MutableStateFlow(TranslateOverviewUiState())
    val state: StateFlow<TranslateOverviewUiState> = _state.asStateFlow()

    init {
        viewModelScope.launch { load(initial = true) }
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
        runCatching { translate.listTranslations(token) }
            .onSuccess { resp ->
                _state.update {
                    it.copy(translations = resp.translations, loading = false)
                }
            }
            .onFailure {
                _state.update { it.copy(loading = false) }
            }
    }

    companion object {
        val Factory: ViewModelProvider.Factory = object : ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : ViewModel> create(modelClass: Class<T>): T =
                TranslateOverviewViewModel() as T
        }
    }
}
