package com.polyglot.android.data.repository

import com.polyglot.android.data.api.LanguagesApi
import com.polyglot.android.data.api.LanguagesResponse
import com.polyglot.android.data.api.MeApi
import com.polyglot.android.data.api.UserDto
import com.polyglot.android.data.api.UserUpdateRequest
import com.polyglot.android.data.api.bearer

class LanguagesRepository(
    private val languagesApi: LanguagesApi,
    private val meApi: MeApi,
) {
    suspend fun languages(token: String): LanguagesResponse = languagesApi.languages(bearer(token))

    suspend fun setNative(token: String, languageId: Long?): UserDto =
        meApi.updateMe(bearer(token), UserUpdateRequest(nativeLanguage = languageId))

    suspend fun setActive(token: String, languageId: Long?): UserDto =
        meApi.updateMe(bearer(token), UserUpdateRequest(activeLanguage = languageId))
}
