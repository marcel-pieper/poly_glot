package com.polyglot.android.data.repository

import com.polyglot.android.data.api.AddVocabRequest
import com.polyglot.android.data.api.AddVocabResponse
import com.polyglot.android.data.api.VocabApi
import com.polyglot.android.data.api.VocabListResponse
import com.polyglot.android.data.api.bearer

class VocabRepository(private val api: VocabApi) {
    suspend fun list(token: String): VocabListResponse =
        api.list(bearer(token))

    suspend fun add(token: String, lemma: String, type: String): AddVocabResponse =
        api.add(bearer(token), AddVocabRequest(lemma = lemma, type = type))

    suspend fun delete(token: String, vocabId: Long) {
        api.delete(bearer(token), vocabId)
    }
}
