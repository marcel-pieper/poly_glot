package com.polyglot.android.data.repository

import com.polyglot.android.data.api.AiApi
import com.polyglot.android.data.api.TranslateRequest
import com.polyglot.android.data.api.TranslateResponse
import com.polyglot.android.data.api.bearer

class TranslateRepository(private val api: AiApi) {
    suspend fun translate(token: String, text: String): TranslateResponse =
        api.translate(bearer(token), TranslateRequest(text = text))
}
