package com.polyglot.android.data.api

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject

// --- auth ---

@Serializable
data class RequestCodeRequest(val email: String)

@Serializable
data class RequestCodeResponse(
    val message: String,
    @SerialName("dev_code") val devCode: String? = null,
)

@Serializable
data class VerifyCodeRequest(val email: String, val code: String)

@Serializable
data class VerifyCodeResponse(
    @SerialName("access_token") val accessToken: String,
    @SerialName("token_type") val tokenType: String = "bearer",
)

// --- user / languages ---

@Serializable
data class UserDto(
    val id: Long,
    val email: String,
    @SerialName("native_language_id") val nativeLanguageId: Long? = null,
    @SerialName("active_language_space_id") val activeLanguageSpaceId: Long? = null,
    @SerialName("is_verified") val isVerified: Boolean,
    @SerialName("created_at") val createdAt: String,
)

@Serializable
data class SupportedLanguageDto(
    val id: Long,
    val code: String,
    val name: String,
    @SerialName("native_name") val nativeName: String? = null,
    @SerialName("learning_enabled") val learningEnabled: Boolean,
)

@Serializable
data class LanguagesResponse(
    @SerialName("native_language") val nativeLanguage: SupportedLanguageDto? = null,
    @SerialName("active_language") val activeLanguage: SupportedLanguageDto? = null,
    @SerialName("all_available_languages") val allAvailableLanguages: List<SupportedLanguageDto>,
)

@Serializable
data class UserUpdateRequest(
    @SerialName("native_language") val nativeLanguage: Long? = null,
    @SerialName("active_language") val activeLanguage: Long? = null,
)

// --- chat ---

@Serializable
data class ThreadDto(
    val id: Long,
    @SerialName("language_space_id") val languageSpaceId: Long,
    val title: String? = null,
    val type: String,
    @SerialName("created_at") val createdAt: String,
    @SerialName("updated_at") val updatedAt: String,
)

@Serializable
data class ThreadListResponse(val threads: List<ThreadDto>, val total: Int)

@Serializable
data class GenerateThreadTitleResponse(val title: String, val generated: Boolean)

@Serializable
data class MessageDto(
    val id: Long,
    @SerialName("thread_id") val threadId: Long,
    val role: String,
    val content: JsonObject,
    @SerialName("created_at") val createdAt: String,
    val metadata: JsonElement? = null,
)

@Serializable
data class MessageListResponse(val messages: List<MessageDto>)

@Serializable
data class SendMessageRequest(
    val text: String? = null,
    @SerialName("starter_id") val starterId: String? = null,
    @SerialName("thread_id") val threadId: Long? = null,
)

@Serializable
data class ConversationStarterItem(
    val id: String,
    @SerialName("display_text") val displayText: String,
)

@Serializable
data class ConversationStartersResponse(val starters: List<ConversationStarterItem>)

@Serializable
data class ExplainSeed(
    @SerialName("source_thread_id") val sourceThreadId: Long,
    @SerialName("source_message_id") val sourceMessageId: Long,
)

@Serializable
data class ExplainSendMessageRequest(
    val text: String,
    @SerialName("thread_id") val threadId: Long? = null,
    val seed: ExplainSeed? = null,
)

@Serializable
data class SendMessageResponse(
    @SerialName("thread_id") val threadId: Long? = null,
    @SerialName("user_message") val userMessage: MessageDto,
    @SerialName("assistant_message") val assistantMessage: MessageDto,
)

// --- ai / translate ---

@Serializable
data class TranslateRequest(val text: String)

@Serializable
data class TranslateResponse(
    @SerialName("source_text") val sourceText: String,
    @SerialName("translated_text") val translatedText: String,
    val status: String,
)
