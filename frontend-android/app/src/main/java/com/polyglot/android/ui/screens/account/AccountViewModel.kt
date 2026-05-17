package com.polyglot.android.ui.screens.account

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.polyglot.android.data.api.SupportedLanguageDto
import com.polyglot.android.data.api.userFacingMessage
import com.polyglot.android.di.ServiceLocator
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.launchIn
import kotlinx.coroutines.flow.onEach
import kotlinx.coroutines.launch

data class AccountUiState(
    val email: String = "",
    val nativeLanguageLabel: String = "Not set",
    val activeLanguageLabel: String = "Not set",
    val nativeLanguageId: Long? = null,
    val activeLanguageId: Long? = null,
    val allLanguages: List<SupportedLanguageDto> = emptyList(),
    val saving: Boolean = false,
    val errorMessage: String? = null,
)

class AccountViewModel : ViewModel() {
    private val auth = ServiceLocator.authRepository
    private val languages = ServiceLocator.languagesRepository
    private val tokenStore = ServiceLocator.tokenStore

    private val _state = MutableStateFlow(AccountUiState())
    val state: StateFlow<AccountUiState> = _state.asStateFlow()

    init {
        combine(auth.userFlow, auth.tokenFlow) { user, token -> user to token }
            .onEach { (user, token) ->
                if (user != null) _state.value = _state.value.copy(email = user.email)
                if (token != null) refreshLanguages(token)
            }
            .launchIn(viewModelScope)
    }

    private suspend fun refreshLanguages(token: String) {
        runCatching { languages.languages(token) }
            .onSuccess { resp ->
                _state.value = _state.value.copy(
                    allLanguages = resp.allAvailableLanguages.sortedBy { it.name },
                    nativeLanguageId = resp.nativeLanguage?.id,
                    activeLanguageId = resp.activeLanguage?.id,
                    nativeLanguageLabel = resp.nativeLanguage?.label() ?: "Not set",
                    activeLanguageLabel = resp.activeLanguage?.label() ?: "Not set",
                )
            }
            .onFailure { err ->
                _state.value = _state.value.copy(
                    errorMessage = err.userFacingMessage("Language load failed"),
                )
            }
    }

    fun setNative(id: Long) = patchLanguage { token -> languages.setNative(token, id) }
    fun setActive(id: Long) = patchLanguage { token -> languages.setActive(token, id) }

    private fun patchLanguage(call: suspend (String) -> Unit) {
        viewModelScope.launch {
            val token = tokenStore.get() ?: return@launch
            _state.value = _state.value.copy(saving = true, errorMessage = null)
            runCatching {
                call(token)
                auth.fetchMe(token)
                refreshLanguages(token)
            }.onFailure { err ->
                _state.value = _state.value.copy(
                    errorMessage = err.userFacingMessage("Failed to update profile"),
                )
            }
            _state.value = _state.value.copy(saving = false)
        }
    }

    fun logout() {
        viewModelScope.launch { auth.logout() }
    }

    fun deleteAccount() {
        viewModelScope.launch {
            val token = tokenStore.get() ?: return@launch
            runCatching { auth.deleteAccount(token) }
                .onFailure { err ->
                    _state.value = _state.value.copy(
                        errorMessage = err.userFacingMessage("Failed to delete account"),
                    )
                }
        }
    }

    companion object {
        val Factory: ViewModelProvider.Factory = object : ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : ViewModel> create(modelClass: Class<T>): T = AccountViewModel() as T
        }
    }
}

private fun SupportedLanguageDto.label(): String = "$name ($code)"
