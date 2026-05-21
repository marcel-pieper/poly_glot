package com.polyglot.android.ui.nav

import androidx.compose.runtime.Composable
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.polyglot.android.ui.screens.chat.ChatScreen
import com.polyglot.android.ui.screens.explain.ExplainScreen
import com.polyglot.android.ui.screens.home.HomeTabsScreen
import com.polyglot.android.ui.screens.translate.TranslationScreen
import com.polyglot.android.ui.screens.vocab.VocabPracticeScreen

@Composable
fun PolyglotNavHost(navController: NavHostController = rememberNavController()) {
    NavHost(navController = navController, startDestination = Routes.Home) {
        composable(Routes.Home) {
            HomeTabsScreen(navController = navController)
        }
        composable(
            route = Routes.Chat,
            arguments = Routes.ChatArgs,
        ) { backStack ->
            val threadId = backStack.arguments?.getString(Routes.ChatArgThreadId)?.toLongOrNull()
            val title = backStack.arguments?.getString(Routes.ChatArgTitle)?.let {
                java.net.URLDecoder.decode(it, "utf-8")
            }
            ChatScreen(
                navController = navController,
                initialThreadId = threadId,
                initialTitle = title,
            )
        }
        composable(
            route = Routes.Explain,
            arguments = Routes.ExplainArgs,
        ) { backStack ->
            val sourceThreadId = backStack.arguments?.getLong(Routes.ExplainArgSourceThread) ?: 0L
            val sourceMessageId = backStack.arguments?.getLong(Routes.ExplainArgSourceMessage) ?: 0L
            ExplainScreen(
                navController = navController,
                sourceThreadId = sourceThreadId,
                sourceMessageId = sourceMessageId,
            )
        }
        composable(
            route = Routes.Translation,
            arguments = Routes.TranslationArgs,
        ) { backStack ->
            val text = backStack.arguments?.getString(Routes.TranslationArg)?.let {
                java.net.URLDecoder.decode(it, "utf-8")
            }.orEmpty()
            TranslationScreen(navController = navController, inputText = text)
        }
        composable(
            route = Routes.TranslationById,
            arguments = Routes.TranslationByIdArgs,
        ) { backStack ->
            val translationId = backStack.arguments?.getLong(Routes.TranslationIdArg) ?: 0L
            TranslationScreen(navController = navController, translationId = translationId)
        }
        composable(Routes.VocabPractice) {
            VocabPracticeScreen(navController = navController)
        }
    }
}
