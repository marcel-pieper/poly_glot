package com.polyglot.android.util

import com.polyglot.android.data.api.MessageDto
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive

/** Best-effort parsing for the dynamic `content` JSON returned by the chat/explain APIs. */

enum class CorrectionStatus { Pending, Complete, Failed, Unknown }

data class Correction(val corrected: String, val notes: List<String>)

data class UserContent(
    val text: String,
    val correctionStatus: CorrectionStatus,
    val correction: Correction?,
)

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
    val status = when (content.str("correction_status")) {
        "pending" -> CorrectionStatus.Pending
        "complete" -> CorrectionStatus.Complete
        "failed" -> CorrectionStatus.Failed
        null -> if (content["correction"] is JsonObject) CorrectionStatus.Complete else CorrectionStatus.Unknown
        else -> CorrectionStatus.Unknown
    }
    return UserContent(text = text, correctionStatus = status, correction = content.parseCorrection())
}

fun MessageDto.parseAssistantText(): String = content.str("assistant_response").orEmpty()

val MessageDto.isUser: Boolean get() = role == "user"
val MessageDto.isAssistant: Boolean get() = role == "assistant"
