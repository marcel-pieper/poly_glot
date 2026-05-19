package com.polyglot.android.ui.screens.chat

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.defaultMinSize
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import android.widget.Toast
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavHostController
import com.polyglot.android.data.api.MessageDto
import com.polyglot.android.ui.components.CorrectionBox
import com.polyglot.android.ui.components.SelectableTranslatableText
import com.polyglot.android.ui.nav.ExplainArgsHolder
import com.polyglot.android.ui.nav.Routes
import com.polyglot.android.ui.theme.Green600
import com.polyglot.android.ui.theme.PaleBlue
import com.polyglot.android.ui.theme.PrimaryBlue
import com.polyglot.android.ui.theme.PrimaryBlueDark
import com.polyglot.android.ui.theme.Slate200
import com.polyglot.android.ui.theme.Slate400
import com.polyglot.android.ui.theme.Slate50
import com.polyglot.android.ui.theme.Slate500
import com.polyglot.android.ui.theme.Slate900
import com.polyglot.android.util.TurnStatus
import com.polyglot.android.util.isUser
import com.polyglot.android.util.parseAssistantContent
import com.polyglot.android.util.parseUserContent

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChatScreen(
    navController: NavHostController,
    initialThreadId: Long?,
    initialTitle: String?,
    viewModel: ChatViewModel = viewModel(factory = ChatViewModel.factory(initialThreadId, initialTitle)),
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    val listState = rememberLazyListState()
    val context = LocalContext.current

    LaunchedEffect(Unit) {
        viewModel.scrollToEnd.collect {
            val count = state.messages.size
            if (count > 0) listState.animateScrollToItem(count - 1)
        }
    }
    LaunchedEffect(Unit) {
        viewModel.errors.collect { msg ->
            Toast.makeText(context, msg, Toast.LENGTH_LONG).show()
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(state.title ?: initialTitle ?: "New chat") },
                navigationIcon = {
                    IconButton(onClick = { navController.popBackStack() }) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                },
            )
        },
        bottomBar = {
            ChatInputBar(
                input = state.input,
                sending = state.sending,
                onInputChange = viewModel::onInputChange,
                onSend = viewModel::sendCurrent,
            )
        },
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .background(Slate50),
        ) {
            if (state.loadingMessages) {
                Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator(color = PrimaryBlue)
                }
            } else {
                Column(modifier = Modifier.fillMaxSize()) {
                    val showStarters = state.starters.isNotEmpty() &&
                        state.threadId == null &&
                        state.messages.isEmpty()
                    if (showStarters) {
                        StartersBlock(
                            starters = state.starters,
                            disabled = state.sending,
                            onStarter = viewModel::sendStarter,
                        )
                    }
                    LazyColumn(
                        state = listState,
                        modifier = Modifier.fillMaxSize(),
                        contentPadding = androidx.compose.foundation.layout.PaddingValues(12.dp),
                        verticalArrangement = Arrangement.spacedBy(10.dp),
                    ) {
                        if (state.messages.isEmpty() && !showStarters) {
                            item {
                                Box(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .padding(top = 60.dp),
                                    contentAlignment = Alignment.Center,
                                ) {
                                    Text(
                                        "Send a message to start the conversation.",
                                        color = Slate400,
                                    )
                                }
                            }
                        }
                        items(state.messages, key = { it.id }) { msg ->
                            MessageRow(
                                msg = msg,
                                threadId = state.threadId,
                                isExpanded = state.expandedCorrections.contains(msg.id),
                                onToggleCorrection = { viewModel.toggleCorrection(msg.id) },
                                onTranslate = { selected ->
                                    navController.navigate(Routes.translation(selected))
                                },
                                onAskExplain = { messageText, correction, sourceThreadId ->
                                    ExplainArgsHolder.put(
                                        ExplainArgsHolder.Args(
                                            sourceThreadId = sourceThreadId,
                                            sourceMessageId = msg.id,
                                            messageText = messageText,
                                            correction = correction,
                                            correctionStatusComplete = true,
                                        ),
                                    )
                                    navController.navigate(Routes.explain(sourceThreadId, msg.id))
                                },
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun StartersBlock(
    starters: List<com.polyglot.android.data.api.ConversationStarterItem>,
    disabled: Boolean,
    onStarter: (String) -> Unit,
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(Color.White)
            .padding(horizontal = 12.dp, vertical = 12.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Text("Start with a preset or type below.", color = Slate500, fontSize = 13.sp)
        FlowRow(
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            starters.forEach { s ->
                Box(
                    modifier = Modifier
                        .background(PaleBlue, RoundedCornerShape(999.dp))
                        .border(1.dp, Color(0xFFBFDBFE), RoundedCornerShape(999.dp))
                        .then(
                            if (disabled) Modifier
                            else Modifier.clickable { onStarter(s.id) },
                        )
                        .padding(horizontal = 14.dp, vertical = 10.dp),
                ) {
                    Text(
                        text = s.displayText,
                        color = PrimaryBlueDark,
                        fontWeight = FontWeight.SemiBold,
                        fontSize = 14.sp,
                    )
                }
            }
        }
    }
    androidx.compose.material3.HorizontalDivider(color = Slate200)
}


@Composable
private fun MessageRow(
    msg: MessageDto,
    threadId: Long?,
    isExpanded: Boolean,
    onToggleCorrection: () -> Unit,
    onTranslate: (String) -> Unit,
    onAskExplain: (messageText: String, correction: com.polyglot.android.util.Correction, sourceThreadId: Long) -> Unit,
) {
    if (msg.isUser) {
        val parsed = msg.parseUserContent()
        Column(
            modifier = Modifier.fillMaxWidth(),
            horizontalAlignment = Alignment.End,
        ) {
            Box(
                modifier = Modifier
                    .widthIn(max = 320.dp)
                    .background(PrimaryBlue, RoundedCornerShape(14.dp))
                    .padding(12.dp),
            ) {
                Text(parsed.text, color = Color.White, fontSize = 15.sp)
            }
            when (parsed.correctionStatus) {
                TurnStatus.Pending -> Box(modifier = Modifier.padding(top = 6.dp)) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(14.dp),
                        strokeWidth = 2.dp,
                        color = Slate500,
                    )
                }
                TurnStatus.Failed -> Text(
                    "Could not generate correction.",
                    color = Slate500,
                    fontSize = 13.sp,
                    modifier = Modifier.padding(top = 6.dp),
                )
                TurnStatus.Complete -> {
                    val correction = parsed.correction
                    if (correction != null) {
                        CorrectionBox(
                            correction = correction,
                            isExpanded = isExpanded,
                            canOpenExplain = threadId != null,
                            onToggle = onToggleCorrection,
                            onAsk = {
                                threadId?.let { tid ->
                                    onAskExplain(parsed.text, correction, tid)
                                }
                            },
                            modifier = Modifier
                                .padding(top = 6.dp)
                                .widthIn(max = 320.dp),
                        )
                    } else {
                        Text("\u2713", color = Green600, fontWeight = FontWeight.Bold, modifier = Modifier.padding(top = 4.dp))
                    }
                }
                TurnStatus.Unknown -> Unit
            }
        }
    } else {
        val parsed = msg.parseAssistantContent()
        Column(modifier = Modifier.fillMaxWidth()) {
            when (parsed.responseStatus) {
                TurnStatus.Pending -> Box(modifier = Modifier.padding(vertical = 6.dp)) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(14.dp),
                        strokeWidth = 2.dp,
                        color = Slate500,
                    )
                }
                TurnStatus.Failed -> Text(
                    "Could not generate a reply.",
                    color = Slate500,
                    fontSize = 13.sp,
                    modifier = Modifier.padding(vertical = 6.dp),
                )
                TurnStatus.Complete, TurnStatus.Unknown -> {
                    Box(modifier = Modifier.fillMaxWidth()) {
                        Box(
                            modifier = Modifier
                                .widthIn(max = 360.dp)
                                .background(Color.White, RoundedCornerShape(14.dp))
                                .border(1.dp, Slate200, RoundedCornerShape(14.dp))
                                .padding(12.dp),
                        ) {
                            SelectableTranslatableText(
                                text = parsed.text,
                                onTranslate = onTranslate,
                                fontSize = 15.sp,
                                color = Slate900,
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun ChatInputBar(
    input: String,
    sending: Boolean,
    onInputChange: (String) -> Unit,
    onSend: () -> Unit,
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .background(Color.White)
            .border(1.dp, Slate200, RoundedCornerShape(0.dp))
            .imePadding()
            .padding(10.dp),
        verticalAlignment = Alignment.Bottom,
        horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        OutlinedTextField(
            value = input,
            onValueChange = onInputChange,
            placeholder = { Text("Type a message\u2026") },
            modifier = Modifier
                .weight(1f)
                .heightIn(min = 44.dp, max = 120.dp),
            enabled = !sending,
        )
        TextButton(
            onClick = onSend,
            enabled = !sending && input.isNotBlank(),
            modifier = Modifier
                .defaultMinSize(minHeight = 44.dp)
                .background(PrimaryBlue, RoundedCornerShape(10.dp)),
        ) {
            if (sending) {
                CircularProgressIndicator(color = Color.White, modifier = Modifier.size(18.dp))
            } else {
                Text("Send", color = Color.White, fontWeight = FontWeight.Bold)
            }
        }
    }
}
