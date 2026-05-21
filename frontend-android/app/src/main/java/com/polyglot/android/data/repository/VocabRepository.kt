package com.polyglot.android.data.repository

import com.polyglot.android.data.api.AddVocabRequest
import com.polyglot.android.data.api.AddVocabResponse
import com.polyglot.android.data.api.PracticeQueueResponse
import com.polyglot.android.data.api.ReviewRequest
import com.polyglot.android.data.api.ReviewResponse
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

    suspend fun practiceQueue(token: String, limit: Int = 50): PracticeQueueResponse =
        api.practiceQueue(bearer(token), limit = limit)

    suspend fun review(token: String, vocabId: Long, rating: String): ReviewResponse =
        api.review(bearer(token), vocabId, ReviewRequest(rating = rating))
}
