package com.polyglot.android.ui.nav

import androidx.navigation.NavType
import androidx.navigation.navArgument
import androidx.navigation.NavHostController
import com.polyglot.android.util.Correction

object Routes {
    const val Home = "home"

    const val ChatArgThreadId = "threadId"
    const val ChatArgTitle = "title"
    const val Chat = "chat?$ChatArgThreadId={$ChatArgThreadId}&$ChatArgTitle={$ChatArgTitle}"

    fun chat(threadId: Long? = null, title: String? = null): String {
        val params = buildList {
            if (threadId != null) add("$ChatArgThreadId=$threadId")
            if (!title.isNullOrEmpty()) add("$ChatArgTitle=${java.net.URLEncoder.encode(title, "utf-8")}")
        }
        return if (params.isEmpty()) "chat" else "chat?" + params.joinToString("&")
    }

    val ChatArgs = listOf(
        navArgument(ChatArgThreadId) {
            type = NavType.StringType
            nullable = true
            defaultValue = null
        },
        navArgument(ChatArgTitle) {
            type = NavType.StringType
            nullable = true
            defaultValue = null
        },
    )

    const val ExplainArgSourceThread = "sourceThreadId"
    const val ExplainArgSourceMessage = "sourceMessageId"
    const val Explain = "explain/{$ExplainArgSourceThread}/{$ExplainArgSourceMessage}"
    fun explain(sourceThreadId: Long, sourceMessageId: Long) =
        "explain/$sourceThreadId/$sourceMessageId"
    val ExplainArgs = listOf(
        navArgument(ExplainArgSourceThread) { type = NavType.LongType },
        navArgument(ExplainArgSourceMessage) { type = NavType.LongType },
    )

    const val TranslationArg = "text"
    const val Translation = "translation/{$TranslationArg}"
    fun translation(text: String) =
        "translation/${java.net.URLEncoder.encode(text, "utf-8")}"
    val TranslationArgs = listOf(
        navArgument(TranslationArg) { type = NavType.StringType },
    )

    const val TranslationIdArg = "translationId"
    const val TranslationById = "translation/id/{$TranslationIdArg}"
    fun translationById(translationId: Long) = "translation/id/$translationId"
    val TranslationByIdArgs = listOf(
        navArgument(TranslationIdArg) { type = NavType.LongType },
    )

    const val VocabPractice = "vocab/practice"
}

/** Transient handoff for ExplainScreen's heavy params (text + correction) without nav serialization. */
object ExplainArgsHolder {
    data class Args(
        val sourceThreadId: Long,
        val sourceMessageId: Long,
        val messageText: String,
        val correction: Correction?,
        val correctionStatusComplete: Boolean,
    )

    private val store = mutableMapOf<Pair<Long, Long>, Args>()

    fun put(args: Args) {
        store[args.sourceThreadId to args.sourceMessageId] = args
    }

    fun get(sourceThreadId: Long, sourceMessageId: Long): Args? =
        store[sourceThreadId to sourceMessageId]
}

fun navigateToExplain(
    navController: NavHostController,
    sourceThreadId: Long,
    sourceMessageId: Long,
    messageText: String,
    correction: Correction?,
) {
    ExplainArgsHolder.put(
        ExplainArgsHolder.Args(
            sourceThreadId = sourceThreadId,
            sourceMessageId = sourceMessageId,
            messageText = messageText,
            correction = correction,
            correctionStatusComplete = true,
        ),
    )
    navController.navigate(Routes.explain(sourceThreadId, sourceMessageId))
}
