package com.polyglot.android.ui.screens.vocab

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
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
import com.polyglot.android.ui.theme.Green600
import com.polyglot.android.ui.theme.PaleBlue
import com.polyglot.android.ui.theme.PrimaryBlue
import com.polyglot.android.ui.theme.Red600
import com.polyglot.android.ui.theme.Red700
import com.polyglot.android.ui.theme.Slate200
import com.polyglot.android.ui.theme.Slate500
import com.polyglot.android.ui.theme.Slate900

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun VocabPracticeScreen(
    navController: NavHostController,
    viewModel: VocabPracticeViewModel = viewModel(factory = VocabPracticeViewModel.Factory),
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    var confirmExit by remember { mutableStateOf(false) }

    val midSession = !state.loading && !state.finished && state.currentItem != null
    fun close() = navController.popBackStack()
    fun maybeClose() {
        if (midSession) confirmExit = true else close()
    }

    BackHandler(enabled = midSession) { confirmExit = true }

    if (confirmExit) {
        AlertDialog(
            onDismissRequest = { confirmExit = false },
            title = { Text("End practice?") },
            text = { Text("You've reviewed ${state.currentIndex - 1} of ${state.total} cards. The rest will stay due.") },
            confirmButton = {
                TextButton(onClick = { confirmExit = false; close() }) {
                    Text("End session")
                }
            },
            dismissButton = {
                TextButton(onClick = { confirmExit = false }) { Text("Keep going") }
            },
        )
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    if (midSession) {
                        Text("Card ${state.currentIndex} / ${state.total}")
                    } else {
                        Text("Vocab practice")
                    }
                },
                navigationIcon = {
                    IconButton(onClick = { maybeClose() }) {
                        Icon(Icons.Filled.Close, contentDescription = "Close")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(),
            )
        },
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .padding(PaddingValues(horizontal = 16.dp, vertical = 12.dp)),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            when {
                state.loading -> Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center,
                ) { CircularProgressIndicator() }

                state.error != null -> ErrorView(
                    message = state.error!!,
                    onRetry = viewModel::retry,
                    onClose = ::close,
                )

                state.finished -> CompletionView(
                    reviewed = state.currentIndex - if (state.total > 0) 1 else 0,
                    total = state.total,
                    correct = state.correctCount,
                    lapsed = state.lapseCount,
                    onClose = ::close,
                )

                state.currentItem != null -> CardArea(
                    item = state.currentItem!!,
                    revealed = state.revealed,
                    grading = state.grading,
                    progress = if (state.total == 0) 0f else (state.currentIndex - 1).toFloat() / state.total.toFloat(),
                    onReveal = viewModel::reveal,
                    onRate = viewModel::rate,
                )
            }
        }
    }
}

@Composable
private fun CardArea(
    item: VocabItemDto,
    revealed: Boolean,
    grading: Boolean,
    progress: Float,
    onReveal: () -> Unit,
    onRate: (Rating) -> Unit,
) {
    LinearProgressIndicator(
        progress = { progress },
        modifier = Modifier.fillMaxWidth(),
        color = PrimaryBlue,
        trackColor = Slate200,
    )

    Card(
        colors = CardDefaults.cardColors(containerColor = Color.White),
        border = BorderStroke(1.dp, Slate200),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                TypePill(item.type)
                Text(
                    item.language,
                    color = Slate500,
                    fontSize = 12.sp,
                    modifier = Modifier.padding(start = 8.dp),
                )
            }
            Text(
                item.lemma,
                color = Slate900,
                fontSize = 28.sp,
                fontWeight = FontWeight.Bold,
            )

            if (revealed) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(PaleBlue, RoundedCornerShape(8.dp))
                        .padding(14.dp),
                ) {
                    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        if (item.glosses.isEmpty()) {
                            Text(
                                "No translations stored yet.",
                                color = Slate500,
                                fontSize = 14.sp,
                            )
                        } else {
                            item.glosses.forEach { gloss ->
                                Text(gloss, color = Slate900, fontSize = 16.sp)
                            }
                        }
                    }
                }
            } else {
                Text(
                    "Try to recall the translation, then reveal.",
                    color = Slate500,
                    fontSize = 13.sp,
                )
            }
        }
    }

    Spacer(modifier = Modifier.height(0.dp))

    if (!revealed) {
        Button(
            onClick = onReveal,
            enabled = !grading,
            colors = ButtonDefaults.buttonColors(containerColor = PrimaryBlue),
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text("Show translation", color = Color.White, fontWeight = FontWeight.Bold)
        }
    } else {
        RatingButtons(grading = grading, onRate = onRate)
    }
}

@Composable
private fun RatingButtons(grading: Boolean, onRate: (Rating) -> Unit) {
    val rows = listOf(
        Rating.Again to Red600,
        Rating.Hard to Slate500,
        Rating.Good to PrimaryBlue,
        Rating.Easy to Green600,
    )
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            rows.take(2).forEach { (rating, color) ->
                RatingButton(
                    rating = rating,
                    container = color,
                    grading = grading,
                    onClick = { onRate(rating) },
                    modifier = Modifier.weight(1f),
                )
            }
        }
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            rows.drop(2).forEach { (rating, color) ->
                RatingButton(
                    rating = rating,
                    container = color,
                    grading = grading,
                    onClick = { onRate(rating) },
                    modifier = Modifier.weight(1f),
                )
            }
        }
    }
}

@Composable
private fun RatingButton(
    rating: Rating,
    container: Color,
    grading: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Button(
        onClick = onClick,
        enabled = !grading,
        colors = ButtonDefaults.buttonColors(containerColor = container),
        modifier = modifier,
    ) {
        Text(rating.label, color = Color.White, fontWeight = FontWeight.SemiBold)
    }
}

@Composable
private fun ErrorView(message: String, onRetry: () -> Unit, onClose: () -> Unit) {
    Card(
        colors = CardDefaults.cardColors(containerColor = Color.White),
        border = BorderStroke(1.dp, Slate200),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            Text("Something went wrong", color = Slate900, fontWeight = FontWeight.Bold)
            Text(message, color = Red700, fontSize = 14.sp)
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(
                    onClick = onRetry,
                    colors = ButtonDefaults.buttonColors(containerColor = PrimaryBlue),
                ) { Text("Retry", color = Color.White) }
                TextButton(onClick = onClose) { Text("Close") }
            }
        }
    }
}

@Composable
private fun CompletionView(
    reviewed: Int,
    total: Int,
    correct: Int,
    lapsed: Int,
    onClose: () -> Unit,
) {
    Box(
        modifier = Modifier.fillMaxSize(),
        contentAlignment = Alignment.Center,
    ) {
        Card(
            colors = CardDefaults.cardColors(containerColor = Color.White),
            border = BorderStroke(1.dp, Slate200),
            modifier = Modifier.fillMaxWidth(),
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(24.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
            ) {
                if (total == 0) {
                    Text("Nothing due", fontSize = 22.sp, fontWeight = FontWeight.Bold, color = Slate900)
                    Text(
                        "You have no vocabulary due for review right now. Add more items from translations or come back later.",
                        color = Slate500,
                        fontSize = 14.sp,
                    )
                } else {
                    Text(
                        "All done!",
                        fontSize = 24.sp,
                        fontWeight = FontWeight.Bold,
                        color = Slate900,
                    )
                    Text(
                        "Reviewed $reviewed of $total card${if (total == 1) "" else "s"}.",
                        color = Slate900,
                        fontSize = 15.sp,
                    )
                    Text(
                        "$correct remembered  ·  $lapsed missed",
                        color = Slate500,
                        fontSize = 13.sp,
                    )
                }
                Button(
                    onClick = onClose,
                    colors = ButtonDefaults.buttonColors(containerColor = PrimaryBlue),
                    modifier = Modifier.fillMaxWidth(),
                ) { Text("Back to vocab", color = Color.White, fontWeight = FontWeight.Bold) }
            }
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
