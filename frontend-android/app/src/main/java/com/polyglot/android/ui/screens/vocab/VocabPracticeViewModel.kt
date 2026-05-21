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

enum class Rating(val apiName: String, val label: String) {
    Again("again", "Again"),
    Hard("hard", "Hard"),
    Good("good", "Good"),
    Easy("easy", "Easy"),
}

data class VocabPracticeUiState(
    val loading: Boolean = true,
    val error: String? = null,
    /** The original queue length; index counts past total when finished. */
    val total: Int = 0,
    val currentIndex: Int = 0,
    val currentItem: VocabItemDto? = null,
    val revealed: Boolean = false,
    val grading: Boolean = false,
    val correctCount: Int = 0,
    val lapseCount: Int = 0,
    val finished: Boolean = false,
)

class VocabPracticeViewModel : ViewModel() {
    private val vocab = ServiceLocator.vocabRepository
    private val tokenStore = ServiceLocator.tokenStore

    private val _state = MutableStateFlow(VocabPracticeUiState())
    val state: StateFlow<VocabPracticeUiState> = _state.asStateFlow()

    private val queue = ArrayDeque<VocabItemDto>()

    init {
        viewModelScope.launch { load() }
    }

    fun retry() {
        viewModelScope.launch {
            _state.update {
                VocabPracticeUiState(loading = true)
            }
            queue.clear()
            load()
        }
    }

    private suspend fun load() {
        val token = tokenStore.get() ?: run {
            _state.update { it.copy(loading = false, error = "Not authenticated") }
            return
        }
        runCatching { vocab.practiceQueue(token) }
            .onSuccess { resp ->
                queue.clear()
                queue.addAll(resp.items)
                _state.update {
                    VocabPracticeUiState(
                        loading = false,
                        total = resp.items.size,
                        currentIndex = if (resp.items.isEmpty()) 0 else 1,
                        currentItem = queue.firstOrNull(),
                        finished = resp.items.isEmpty(),
                    )
                }
            }
            .onFailure { err ->
                _state.update {
                    it.copy(
                        loading = false,
                        error = err.userFacingMessage("Could not start practice"),
                    )
                }
            }
    }

    fun reveal() {
        if (_state.value.revealed || _state.value.currentItem == null) return
        _state.update { it.copy(revealed = true) }
    }

    fun rate(rating: Rating) {
        val current = _state.value.currentItem ?: return
        if (_state.value.grading) return
        _state.update { it.copy(grading = true) }
        viewModelScope.launch {
            val token = tokenStore.get() ?: run {
                _state.update { it.copy(grading = false, error = "Not authenticated") }
                return@launch
            }
            runCatching { vocab.review(token, current.id, rating.apiName) }
                .onSuccess { _ ->
                    queue.removeFirstOrNull()
                    val next = queue.firstOrNull()
                    val s = _state.value
                    _state.update {
                        if (next == null) {
                            it.copy(
                                grading = false,
                                revealed = false,
                                currentItem = null,
                                correctCount = s.correctCount + if (rating != Rating.Again) 1 else 0,
                                lapseCount = s.lapseCount + if (rating == Rating.Again) 1 else 0,
                                finished = true,
                            )
                        } else {
                            it.copy(
                                grading = false,
                                revealed = false,
                                currentItem = next,
                                currentIndex = it.currentIndex + 1,
                                correctCount = s.correctCount + if (rating != Rating.Again) 1 else 0,
                                lapseCount = s.lapseCount + if (rating == Rating.Again) 1 else 0,
                            )
                        }
                    }
                }
                .onFailure { err ->
                    _state.update {
                        it.copy(
                            grading = false,
                            error = err.userFacingMessage("Could not save your answer"),
                        )
                    }
                }
        }
    }

    companion object {
        val Factory: ViewModelProvider.Factory = object : ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : ViewModel> create(modelClass: Class<T>): T =
                VocabPracticeViewModel() as T
        }
    }
}
