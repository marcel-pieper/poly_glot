package com.polyglot.android.ui.screens.chat

import androidx.compose.foundation.background
import androidx.compose.foundation.combinedClickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.pulltorefresh.PullToRefreshBox
import androidx.compose.material3.pulltorefresh.rememberPullToRefreshState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavHostController
import com.polyglot.android.data.api.ThreadDto
import com.polyglot.android.ui.nav.Routes
import com.polyglot.android.ui.theme.PrimaryBlue
import com.polyglot.android.ui.theme.Red600
import com.polyglot.android.ui.theme.Slate500
import com.polyglot.android.ui.theme.Slate900

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChatOverviewScreen(
    navController: NavHostController,
    viewModel: ChatOverviewViewModel = viewModel(factory = ChatOverviewViewModel.Factory),
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    var pendingDelete by remember { mutableStateOf<ThreadDto?>(null) }

    if (state.loading) {
        Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            CircularProgressIndicator()
        }
        return
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(PaddingValues(16.dp)),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        Button(
            onClick = {
                navController.navigate(Routes.chat(threadId = null, title = "New chat"))
            },
            colors = ButtonDefaults.buttonColors(containerColor = PrimaryBlue),
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text("Start Chat", color = Color.White, fontWeight = FontWeight.Bold)
        }

        Text("Previous chats", fontWeight = FontWeight.Bold, color = Slate900, fontSize = 16.sp)

        val ptrState = rememberPullToRefreshState()
        PullToRefreshBox(
            isRefreshing = state.refreshing,
            onRefresh = viewModel::refresh,
            state = ptrState,
            modifier = Modifier.fillMaxSize(),
        ) {
            if (state.threads.isEmpty()) {
                LazyColumn { item { EmptyState() } }
            } else {
                LazyColumn(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    items(state.threads, key = { it.id }) { thread ->
                        ThreadRow(
                            thread = thread,
                            generatingTitle = state.titlingThreadIds.contains(thread.id),
                            deleting = state.deletingThreadId == thread.id,
                            onClick = {
                                navController.navigate(
                                    Routes.chat(
                                        threadId = thread.id,
                                        title = thread.title ?: "Chat ${thread.id}",
                                    ),
                                )
                            },
                            onLongPress = { pendingDelete = thread },
                        )
                    }
                }
            }
        }
    }

    pendingDelete?.let { thread ->
        AlertDialog(
            onDismissRequest = { pendingDelete = null },
            title = { Text("Delete chat?") },
            text = { Text("This will permanently remove this conversation.") },
            confirmButton = {
                TextButton(onClick = {
                    pendingDelete = null
                    viewModel.delete(thread)
                }) {
                    Text("Delete", color = Red600)
                }
            },
            dismissButton = {
                TextButton(onClick = { pendingDelete = null }) { Text("Cancel") }
            },
        )
    }
}

@Composable
private fun EmptyState() {
    Card(
        colors = CardDefaults.cardColors(containerColor = Color.White),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Text("No chats yet", fontWeight = FontWeight.Bold, color = Slate900)
            Text("Start your first chat to see it here.", color = Slate500, fontSize = 13.sp)
        }
    }
}

@OptIn(androidx.compose.foundation.ExperimentalFoundationApi::class)
@Composable
private fun ThreadRow(
    thread: ThreadDto,
    generatingTitle: Boolean,
    deleting: Boolean,
    onClick: () -> Unit,
    onLongPress: () -> Unit,
) {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .alpha(if (deleting) 0.5f else 1f)
            .background(Color.White, RoundedCornerShape(10.dp))
            .combinedClickable(onClick = onClick, onLongClick = onLongPress)
            .padding(14.dp),
    ) {
        Column {
            Row(
                generatingTitle = generatingTitle,
                title = thread.title ?: "Chat ${thread.id}",
            )
            Text(
                thread.updatedAt,
                color = Slate500,
                fontSize = 12.sp,
                modifier = Modifier.padding(top = 4.dp),
            )
        }
    }
}

@Composable
private fun Row(generatingTitle: Boolean, title: String) {
    androidx.compose.foundation.layout.Row(
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        if (generatingTitle) {
            CircularProgressIndicator(modifier = Modifier.size(14.dp), strokeWidth = 2.dp)
        }
        Text(
            title,
            fontWeight = FontWeight.Bold,
            color = Slate900,
            modifier = Modifier.alpha(if (generatingTitle) 0.65f else 1f),
        )
    }
}
