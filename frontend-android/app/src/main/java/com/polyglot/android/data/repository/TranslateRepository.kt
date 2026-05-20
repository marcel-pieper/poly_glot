package com.polyglot.android.data.repository

import com.polyglot.android.data.api.AiApi
import com.polyglot.android.data.api.TranslateRequest
import com.polyglot.android.data.api.TranslateResponse
import com.polyglot.android.data.api.TranslationListResponse
import com.polyglot.android.data.api.bearer

class TranslateRepository(private val api: AiApi) {
    suspend fun translate(token: String, text: String): TranslateResponse =
        api.translate(bearer(token), TranslateRequest(text = text))

    suspend fun listTranslations(token: String, limit: Int = 50, offset: Int = 0): TranslationListResponse =
        api.listTranslations(bearer(token), limit = limit, offset = offset)

    suspend fun getTranslation(token: String, translationId: Long): TranslateResponse =
        api.getTranslation(bearer(token), translationId)
}
