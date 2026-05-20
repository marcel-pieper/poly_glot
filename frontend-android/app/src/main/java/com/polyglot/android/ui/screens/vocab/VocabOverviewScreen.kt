package com.polyglot.android.ui.screens.vocab

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Text
import androidx.compose.material3.pulltorefresh.PullToRefreshBox
import androidx.compose.material3.pulltorefresh.rememberPullToRefreshState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavHostController
import com.polyglot.android.data.api.VocabItemDto
import com.polyglot.android.ui.theme.PrimaryBlue
import com.polyglot.android.ui.theme.Red700
import com.polyglot.android.ui.theme.Slate200
import com.polyglot.android.ui.theme.Slate500
import com.polyglot.android.ui.theme.Slate900

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun VocabOverviewScreen(
    @Suppress("UNUSED_PARAMETER") navController: NavHostController,
    isTabVisible: Boolean = true,
    viewModel: VocabOverviewViewModel = viewModel(factory = VocabOverviewViewModel.Factory),
) {
    val state by viewModel.state.collectAsStateWithLifecycle()

    LaunchedEffect(isTabVisible) {
        if (isTabVisible) viewModel.refresh()
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(PaddingValues(16.dp)),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        Text("Vocabulary", fontSize = 16.sp, fontWeight = FontWeight.Bold, color = Slate900)

        Button(
            onClick = { /* TODO: start vocab practice session */ },
            enabled = false,
            colors = ButtonDefaults.buttonColors(
                containerColor = PrimaryBlue,
                disabledContainerColor = Color(0xFF93C5FD),
            ),
            modifier = Modifier.fillMaxWidth(),
        ) {
            val label = if (state.dueCount > 0) {
                "Start vocab practice (${state.dueCount} due)"
            } else {
                "Start vocab practice"
            }
            Text(label, color = Color.White, fontWeight = FontWeight.Bold)
        }

        if (!state.loading && state.items.isNotEmpty()) {
            Text(
                "${state.items.size} item(s) in your list",
                color = Slate500,
                fontSize = 12.sp,
            )
        }

        val ptrState = rememberPullToRefreshState()
        PullToRefreshBox(
            isRefreshing = state.refreshing,
            onRefresh = viewModel::refresh,
            state = ptrState,
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth(),
        ) {
            when {
                state.loading -> Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center,
                ) {
                    CircularProgressIndicator()
                }

                state.error != null && state.items.isEmpty() -> ErrorCard(state.error!!)

                state.items.isEmpty() -> EmptyVocabCard()

                else -> LazyColumn(
                    modifier = Modifier.fillMaxSize(),
                    verticalArrangement = Arrangement.spacedBy(10.dp),
                ) {
                    items(state.items, key = { it.id }) { item -> VocabRow(item) }
                }
            }
        }
    }
}

@Composable
private fun EmptyVocabCard() {
    Card(
        colors = CardDefaults.cardColors(containerColor = Color.White),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Text("No vocabulary yet", fontWeight = FontWeight.Bold, color = Slate900)
            Text(
                "Translate something, then tap the + on any item to add it to your vocabulary.",
                color = Slate500,
                fontSize = 13.sp,
            )
        }
    }
}

@Composable
private fun ErrorCard(message: String) {
    Card(
        colors = CardDefaults.cardColors(containerColor = Color.White),
        border = BorderStroke(1.dp, Slate200),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Text(message, modifier = Modifier.padding(14.dp), color = Red700, fontSize = 13.sp)
    }
}

@Composable
private fun VocabRow(item: VocabItemDto) {
    Card(
        colors = CardDefaults.cardColors(containerColor = Color.White),
        border = BorderStroke(1.dp, Slate200),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(modifier = Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                TypePill(item.type)
                Text(
                    item.lemma,
                    color = Slate900,
                    fontWeight = FontWeight.Bold,
                    fontSize = 16.sp,
                    modifier = Modifier.padding(start = 8.dp),
                )
                if (item.isDue) {
                    Box(modifier = Modifier.padding(start = 8.dp)) { DuePill() }
                }
            }

            if (item.glosses.isNotEmpty()) {
                Text(
                    item.glosses.joinToString(", "),
                    color = Slate900,
                    fontSize = 14.sp,
                )
            }

            Text(
                metadataLine(item),
                color = Slate500,
                fontSize = 11.sp,
            )
        }
    }
}

@Composable
private fun TypePill(type: String) {
    Box(
        modifier = Modifier
            .border(BorderStroke(1.dp, Slate200), RoundedCornerShape(4.dp))
            .padding(horizontal = 6.dp, vertical = 2.dp),
    ) {
        Text(type.uppercase(), color = Slate500, fontSize = 10.sp, fontWeight = FontWeight.SemiBold)
    }
}

@Composable
private fun DuePill() {
    Box(
        modifier = Modifier
            .border(BorderStroke(1.dp, PrimaryBlue), RoundedCornerShape(4.dp))
            .padding(horizontal = 6.dp, vertical = 2.dp),
    ) {
        Text("DUE", color = PrimaryBlue, fontSize = 10.sp, fontWeight = FontWeight.SemiBold)
    }
}

private fun metadataLine(item: VocabItemDto): String {
    val parts = mutableListOf<String>()
    parts += "due ${shortDate(item.due)}"
    item.lastReview?.let { parts += "last reviewed ${shortDate(it)}" }
    if (item.reviewCount > 0 || item.lapseCount > 0) {
        parts += "${item.reviewCount} reviews · ${item.lapseCount} lapses"
    }
    parts += stateLabel(item.state)
    return parts.joinToString("  ·  ")
}

private fun shortDate(iso: String): String {
    val t = iso.indexOf('T')
    if (t < 0) return iso
    val date = iso.substring(0, t)
    val rest = iso.substring(t + 1)
    val time = rest.take(5)
    return "$date $time"
}

private fun stateLabel(state: Int): String = when (state) {
    1 -> "learning"
    2 -> "review"
    3 -> "relearning"
    else -> "state $state"
}
