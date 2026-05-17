package com.polyglot.android.ui.screens.login

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.polyglot.android.data.api.SupportedLanguageDto
import com.polyglot.android.data.api.UserUpdateRequest
import com.polyglot.android.data.api.bearer
import com.polyglot.android.data.api.userFacingMessage
import com.polyglot.android.di.ServiceLocator
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

enum class LoginStep { Email, Code, NativeLanguage, ActiveLanguage }

data class LoginLanguageOption(val id: Long, val name: String)

data class LoginUiState(
    val step: LoginStep = LoginStep.Email,
    val email: String = "",
    val code: String = "",
    val busy: Boolean = false,
    val message: String = "",
    val devCode: String? = null,
    val pendingToken: String? = null,
    val allLanguages: List<SupportedLanguageDto> = emptyList(),
    val nativeLanguageId: Long? = null,
    val activeLanguageId: Long? = null,
) {
    val nativeOptions: List<LoginLanguageOption>
        get() = allLanguages
            .filter { it.id != activeLanguageId }
            .map { LoginLanguageOption(it.id, it.name) }

    val activeOptions: List<LoginLanguageOption>
        get() = allLanguages
            .filter { it.learningEnabled && it.id != nativeLanguageId }
            .map { LoginLanguageOption(it.id, it.name) }
}

class LoginViewModel : ViewModel() {
    private val auth = ServiceLocator.authRepository
    private val languages = ServiceLocator.languagesRepository
    private val meApi = ServiceLocator.meApi

    private val _state = MutableStateFlow(LoginUiState())
    val state: StateFlow<LoginUiState> = _state.asStateFlow()

    fun onEmailChange(value: String) = _state.update { it.copy(email = value) }
    fun onCodeChange(value: String) = _state.update { it.copy(code = value.take(6)) }

    fun requestCode() {
        val email = _state.value.email.trim().lowercase()
        if (email.isEmpty()) {
            _state.update { it.copy(message = "Enter your email first.") }
            return
        }
        viewModelScope.launch {
            _state.update { it.copy(busy = true, message = "", devCode = null) }
            runCatching { auth.requestCode(email) }
                .onSuccess { resp ->
                    _state.update {
                        it.copy(
                            busy = false,
                            step = LoginStep.Code,
                            message = resp.message,
                            devCode = resp.devCode,
                        )
                    }
                }
                .onFailure { err ->
                    _state.update {
                        it.copy(busy = false, message = err.userFacingMessage("Failed to request code"))
                    }
                }
        }
    }

    fun verifyCode() {
        val email = _state.value.email.trim().lowercase()
        val code = _state.value.code.trim()
        if (email.isEmpty() || code.length != 6) {
            _state.update { it.copy(message = "Enter a valid email and 6-digit code.") }
            return
        }
        viewModelScope.launch {
            _state.update { it.copy(busy = true, message = "") }
            runCatching {
                val token = auth.verifyCode(email, code)
                val me = meApi.me(bearer(token))
                val langs = languages.languages(token)
                Triple(token, me, langs)
            }.onSuccess { (token, _, langs) ->
                val next = when {
                    langs.nativeLanguage == null -> LoginStep.NativeLanguage
                    langs.activeLanguage == null -> LoginStep.ActiveLanguage
                    else -> null
                }
                if (next == null) {
                    auth.loginWith(token)
                } else {
                    _state.update {
                        it.copy(
                            busy = false,
                            step = next,
                            pendingToken = token,
                            allLanguages = langs.allAvailableLanguages,
                            nativeLanguageId = langs.nativeLanguage?.id,
                            activeLanguageId = langs.activeLanguage?.id,
                            code = "",
                            message = "",
                        )
                    }
                }
            }.onFailure { err ->
                _state.update {
                    it.copy(busy = false, message = err.userFacingMessage("Failed to verify code"))
                }
            }
        }
    }

    fun selectNative(languageId: Long) {
        val token = _state.value.pendingToken ?: return
        viewModelScope.launch {
            _state.update { it.copy(busy = true) }
            runCatching {
                meApi.updateMe(bearer(token), UserUpdateRequest(nativeLanguage = languageId))
                languages.languages(token)
            }.onSuccess { langs ->
                _state.update {
                    it.copy(
                        busy = false,
                        step = LoginStep.ActiveLanguage,
                        allLanguages = langs.allAvailableLanguages,
                        nativeLanguageId = langs.nativeLanguage?.id,
                        activeLanguageId = langs.activeLanguage?.id,
                    )
                }
            }.onFailure { err ->
                _state.update {
                    it.copy(busy = false, message = err.userFacingMessage("Failed to set native language"))
                }
            }
        }
    }

    fun selectActive(languageId: Long) {
        val token = _state.value.pendingToken ?: return
        viewModelScope.launch {
            _state.update { it.copy(busy = true) }
            runCatching {
                meApi.updateMe(bearer(token), UserUpdateRequest(activeLanguage = languageId))
            }.onSuccess {
                auth.loginWith(token)
            }.onFailure { err ->
                _state.update {
                    it.copy(busy = false, message = err.userFacingMessage("Failed to set active language"))
                }
            }
        }
    }

    fun goBackToNativeStep() {
        _state.update { it.copy(step = LoginStep.NativeLanguage, message = "") }
    }

    companion object {
        val Factory: ViewModelProvider.Factory = object : ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : ViewModel> create(modelClass: Class<T>): T = LoginViewModel() as T
        }
    }
}
