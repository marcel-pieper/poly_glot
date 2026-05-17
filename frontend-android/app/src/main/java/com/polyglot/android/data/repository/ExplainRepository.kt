package com.polyglot.android.data.repository

import com.polyglot.android.data.api.ExplainApi
import com.polyglot.android.data.api.ExplainSeed
import com.polyglot.android.data.api.ExplainSendMessageRequest
import com.polyglot.android.data.api.MessageDto
import com.polyglot.android.data.api.SendMessageResponse
import com.polyglot.android.data.api.bearer

class ExplainRepository(private val api: ExplainApi) {

    suspend fun messages(token: String, threadId: Long): List<MessageDto> =
        api.messages(bearer(token), threadId).messages

    suspend fun send(
        token: String,
        text: String,
        threadId: Long?,
        seed: ExplainSeed?,
    ): SendMessageResponse =
        api.send(
            bearer(token),
            ExplainSendMessageRequest(text = text, threadId = threadId, seed = seed),
        )
}
