package com.polyglot.android.util

import com.polyglot.android.data.api.MessageDto
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive

/** Best-effort parsing for the dynamic `content` JSON returned by the chat/explain APIs. */

enum class TurnStatus { Pending, Complete, Failed, Unknown }

data class Correction(val corrected: String, val notes: List<String>)

data class UserContent(
    val text: String,
    val correctionStatus: TurnStatus,
    val correction: Correction?,
)

data class AssistantContent(
    val text: String,
    val responseStatus: TurnStatus,
)

private fun JsonObject.parseTurnStatus(key: String, fallbackWhenMissing: TurnStatus): TurnStatus =
    when (str(key)) {
        "pending" -> TurnStatus.Pending
        "complete" -> TurnStatus.Complete
        "failed" -> TurnStatus.Failed
        null -> fallbackWhenMissing
        else -> TurnStatus.Unknown
    }

private fun JsonObject.str(key: String): String? =
    (this[key] as? JsonPrimitive)?.takeIf { it.isString }?.content

private fun JsonObject.parseCorrection(): Correction? {
    val obj = this["correction"] as? JsonObject ?: return null
    val corrected = obj.str("corrected").orEmpty()
    val notes = (obj["notes"] as? JsonArray)?.mapNotNull {
        (it as? JsonPrimitive)?.takeIf(JsonPrimitive::isString)?.content
    }.orEmpty()
    return Correction(corrected = corrected, notes = notes)
}

fun MessageDto.parseUserContent(): UserContent {
    val text = content.str("text").orEmpty()
    val fallback = if (content["correction"] is JsonObject) TurnStatus.Complete else TurnStatus.Unknown
    val status = content.parseTurnStatus("correction_status", fallback)
    return UserContent(text = text, correctionStatus = status, correction = content.parseCorrection())
}

fun MessageDto.parseAssistantContent(): AssistantContent {
    val text = content.str("assistant_response").orEmpty()
    val fallback = if (text.isNotEmpty()) TurnStatus.Complete else TurnStatus.Unknown
    val status = content.parseTurnStatus("response_status", fallback)
    return AssistantContent(text = text, responseStatus = status)
}

@Deprecated("Use parseAssistantContent()", ReplaceWith("parseAssistantContent().text"))
fun MessageDto.parseAssistantText(): String = parseAssistantContent().text

val MessageDto.isUser: Boolean get() = role == "user"
val MessageDto.isAssistant: Boolean get() = role == "assistant"
