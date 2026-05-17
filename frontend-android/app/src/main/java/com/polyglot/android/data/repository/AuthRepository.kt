package com.polyglot.android.data.repository

import com.polyglot.android.data.api.AuthApi
import com.polyglot.android.data.api.MeApi
import com.polyglot.android.data.api.RequestCodeRequest
import com.polyglot.android.data.api.RequestCodeResponse
import com.polyglot.android.data.api.UserDto
import com.polyglot.android.data.api.VerifyCodeRequest
import com.polyglot.android.data.api.bearer
import com.polyglot.android.data.store.TokenStore
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.launchIn
import kotlinx.coroutines.flow.onEach

class AuthRepository(
    private val authApi: AuthApi,
    private val meApi: MeApi,
    private val tokenStore: TokenStore,
) {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)

    private val _token = MutableStateFlow<String?>(null)
    val tokenFlow: Flow<String?> = _token.asStateFlow()

    private val _user = MutableStateFlow<UserDto?>(null)
    val userFlow: Flow<UserDto?> = _user.asStateFlow()

    private val _ready = MutableStateFlow(false)
    val readyFlow: Flow<Boolean> = _ready.asStateFlow()

    init {
        tokenStore.tokenFlow
            .onEach { stored ->
                _token.value = stored
                if (stored != null) {
                    runCatching { _user.value = meApi.me(bearer(stored)) }
                        .onFailure {
                            tokenStore.clear()
                            _user.value = null
                        }
                } else {
                    _user.value = null
                }
                _ready.value = true
            }
            .launchIn(scope)
    }

    suspend fun requestCode(email: String): RequestCodeResponse =
        authApi.requestCode(RequestCodeRequest(email = email))

    /** Verifies the 6-digit code and returns the access token without yet persisting it. */
    suspend fun verifyCode(email: String, code: String): String =
        authApi.verifyCode(VerifyCodeRequest(email = email, code = code)).accessToken

    /** Persists the token, kicking off the userFlow refresh via tokenStore.tokenFlow. */
    suspend fun loginWith(token: String) {
        tokenStore.set(token)
    }

    suspend fun logout() {
        tokenStore.clear()
    }

    suspend fun deleteAccount(token: String) {
        meApi.deleteMe(bearer(token))
        tokenStore.clear()
    }

    suspend fun fetchMe(token: String): UserDto {
        val u = meApi.me(bearer(token))
        _user.value = u
        return u
    }
}
