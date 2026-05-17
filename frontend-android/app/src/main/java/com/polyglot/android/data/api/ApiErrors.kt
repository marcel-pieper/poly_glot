package com.polyglot.android.data.api

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import retrofit2.HttpException

private val ErrorJson = Json { ignoreUnknownKeys = true; isLenient = true }

/**
 * Extracts the FastAPI `{ "detail": ... }` message from an HttpException, falling back to the
 * cause's localized message when parsing fails.
 */
fun Throwable.userFacingMessage(default: String = "Request failed"): String {
    if (this is HttpException) {
        val raw = response()?.errorBody()?.string().orEmpty()
        runCatching {
            val root = ErrorJson.parseToJsonElement(raw)
            if (root is JsonObject) {
                when (val d = root["detail"]) {
                    is JsonPrimitive -> return d.content
                    is JsonArray -> {
                        val first = d.firstOrNull() as? JsonObject
                        val msg = (first?.get("msg") as? JsonPrimitive)?.content
                        if (!msg.isNullOrBlank()) return msg
                    }
                    null -> Unit
                    else -> return d.toString()
                }
            }
        }
    }
    return localizedMessage ?: default
}

fun bearer(token: String): String = "Bearer $token"
