package com.polyglot.android.data.repository

import com.polyglot.android.data.api.ChatApi
import com.polyglot.android.data.api.ConversationStarterItem
import com.polyglot.android.data.api.MessageDto
import com.polyglot.android.data.api.SendMessageRequest
import com.polyglot.android.data.api.SendMessageResponse
import com.polyglot.android.data.api.ThreadDto
import com.polyglot.android.data.api.bearer

class ChatRepository(private val api: ChatApi) {

    suspend fun starters(token: String): List<ConversationStarterItem> =
        api.starters(bearer(token)).starters

    suspend fun threads(token: String): List<ThreadDto> = api.threads(bearer(token)).threads

    suspend fun messages(token: String, threadId: Long): List<MessageDto> =
        api.messages(bearer(token), threadId).messages

    suspend fun delete(token: String, threadId: Long) = api.deleteThread(bearer(token), threadId)

    suspend fun generateTitle(token: String, threadId: Long): String? =
        runCatching { api.generateTitle(bearer(token), threadId).title }.getOrNull()

    suspend fun sendText(token: String, threadId: Long?, text: String): SendMessageResponse =
        api.send(bearer(token), SendMessageRequest(text = text, threadId = threadId))

    suspend fun sendStarter(token: String, starterId: String): SendMessageResponse =
        api.send(bearer(token), SendMessageRequest(starterId = starterId))
}
