package com.polyglot.android.ui.screens.translate

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.defaultMinSize
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.pulltorefresh.PullToRefreshBox
import androidx.compose.material3.pulltorefresh.rememberPullToRefreshState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavHostController
import com.polyglot.android.data.api.TranslationSummaryDto
import com.polyglot.android.ui.nav.Routes
import com.polyglot.android.ui.theme.PrimaryBlue
import com.polyglot.android.ui.theme.Slate500
import com.polyglot.android.ui.theme.Slate900

private const val PREVIEW_MAX_CHARS = 120

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TranslateOverviewScreen(
    navController: NavHostController,
    isTabVisible: Boolean = true,
    viewModel: TranslateOverviewViewModel = viewModel(factory = TranslateOverviewViewModel.Factory),
) {
    var input by rememberSaveable { mutableStateOf("") }
    val state by viewModel.state.collectAsStateWithLifecycle()
    var hasBeenVisible by remember { mutableStateOf(false) }

    LaunchedEffect(isTabVisible) {
        if (!isTabVisible) return@LaunchedEffect
        if (hasBeenVisible) {
            viewModel.refresh()
        } else {
            hasBeenVisible = true
        }
    }
    val trimmed = remember(input) { input.trim() }
    val canTranslate = trimmed.isNotEmpty()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(PaddingValues(16.dp)),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text("Translate", fontSize = 16.sp, fontWeight = FontWeight.Bold, color = Slate900)
        OutlinedTextField(
            value = input,
            onValueChange = { input = it },
            placeholder = { Text("Type text to translate...") },
            modifier = Modifier
                .fillMaxWidth()
                .defaultMinSize(minHeight = 96.dp),
        )
        Button(
            onClick = {
                val v = trimmed
                if (v.isEmpty()) return@Button
                input = ""
                navController.navigate(Routes.translation(v))
            },
            enabled = canTranslate,
            colors = ButtonDefaults.buttonColors(
                containerColor = PrimaryBlue,
                disabledContainerColor = Color(0xFF93C5FD),
            ),
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text("Translate", color = Color.White, fontWeight = FontWeight.Bold)
        }

        Text("Previous translations", fontSize = 16.sp, fontWeight = FontWeight.Bold, color = Slate900)

        Box(modifier = Modifier.fillMaxSize()) {
        when {
            state.loading -> {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center,
                ) {
                    CircularProgressIndicator()
                }
            }
            else -> {
                val ptrState = rememberPullToRefreshState()
                PullToRefreshBox(
                    isRefreshing = state.refreshing,
                    onRefresh = viewModel::refresh,
                    state = ptrState,
                    modifier = Modifier.fillMaxSize(),
                ) {
                    if (state.translations.isEmpty()) {
                        EmptyTranslationsCard()
                    } else {
                        LazyColumn(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                            items(state.translations, key = { it.id }) { summary ->
                                TranslationSummaryRow(
                                    summary = summary,
                                    onClick = {
                                        navController.navigate(Routes.translationById(summary.id))
                                    },
                                )
                            }
                        }
                    }
                }
            }
        }
        }
    }
}

@Composable
private fun EmptyTranslationsCard() {
    Card(
        colors = CardDefaults.cardColors(containerColor = Color.White),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Text("No translations yet", fontWeight = FontWeight.Bold, color = Slate900)
            Text(
                "Translations you save while signed in with a language space will appear here.",
                color = Slate500,
                fontSize = 13.sp,
            )
        }
    }
}

@Composable
private fun TranslationSummaryRow(summary: TranslationSummaryDto, onClick: () -> Unit) {
    Card(
        onClick = onClick,
        colors = CardDefaults.cardColors(containerColor = Color.White),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(modifier = Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Text(
                preview(summary.sourceText),
                color = Slate900,
                fontSize = 15.sp,
                fontWeight = FontWeight.SemiBold,
                maxLines = 2,
                overflow = TextOverflow.Ellipsis,
            )
            Text(
                preview(summary.translatedText),
                color = Slate500,
                fontSize = 14.sp,
                maxLines = 2,
                overflow = TextOverflow.Ellipsis,
            )
        }
    }
}

private fun preview(text: String): String {
    val t = text.trim()
    if (t.length <= PREVIEW_MAX_CHARS) return t
    return t.take(PREVIEW_MAX_CHARS) + "…"
}
