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
data class ExplainThreadLookupResponse(
    @SerialName("thread_id") val threadId: Long? = null,
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
data class TranslateItemDto(
    val type: String,
    @SerialName("raw_item") val rawItem: String,
    @SerialName("raw_item_translation") val rawItemTranslation: String,
    val lemma: String,
)

@Serializable
data class TranslateResponse(
    @SerialName("translation_id") val translationId: Long? = null,
    @SerialName("source_text") val sourceText: String,
    @SerialName("translated_text") val translatedText: String,
    val status: String,
    val items: List<TranslateItemDto> = emptyList(),
)

@Serializable
data class TranslationSummaryDto(
    val id: Long,
    @SerialName("source_text") val sourceText: String,
    @SerialName("translated_text") val translatedText: String,
    @SerialName("from_language") val fromLanguage: String,
    @SerialName("to_language") val toLanguage: String,
    @SerialName("created_at") val createdAt: String,
)

@Serializable
data class TranslationListResponse(
    val translations: List<TranslationSummaryDto>,
    val total: Int,
)

// --- vocab ---

@Serializable
data class AddVocabRequest(
    val lemma: String,
    val type: String,
)

@Serializable
data class VocabItemDto(
    val id: Long,
    @SerialName("lemma_id") val lemmaId: Long,
    val lemma: String,
    val type: String,
    val language: String,
    val glosses: List<String> = emptyList(),
    val state: Int,
    val due: String,
    @SerialName("last_review") val lastReview: String? = null,
    @SerialName("review_count") val reviewCount: Int,
    @SerialName("lapse_count") val lapseCount: Int,
    @SerialName("is_due") val isDue: Boolean,
)

@Serializable
data class VocabListResponse(
    val items: List<VocabItemDto>,
    val total: Int,
    @SerialName("due_count") val dueCount: Int,
)

@Serializable
data class AddVocabResponse(
    val item: VocabItemDto,
    val created: Boolean,
)

@Serializable
data class PracticeQueueResponse(
    val items: List<VocabItemDto>,
    val total: Int,
)

@Serializable
data class ReviewRequest(val rating: String)

@Serializable
data class ReviewResponse(val item: VocabItemDto)
