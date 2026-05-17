package com.polyglot.android.ui.screens.explain

import android.widget.Toast
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
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
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavHostController
import com.polyglot.android.data.api.MessageDto
import com.polyglot.android.ui.nav.ExplainArgsHolder
import com.polyglot.android.ui.theme.PrimaryBlue
import com.polyglot.android.ui.theme.Slate200
import com.polyglot.android.ui.theme.Slate500
import com.polyglot.android.ui.theme.Slate50
import com.polyglot.android.ui.theme.Slate900
import com.polyglot.android.ui.theme.Stone700
import com.polyglot.android.ui.theme.Stone900
import com.polyglot.android.util.isAssistant
import com.polyglot.android.util.parseAssistantText
import com.polyglot.android.util.parseUserContent

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ExplainScreen(
    navController: NavHostController,
    sourceThreadId: Long,
    sourceMessageId: Long,
) {
    val args = remember(sourceThreadId, sourceMessageId) {
        ExplainArgsHolder.get(sourceThreadId, sourceMessageId)
    }
    val viewModel: ExplainViewModel = viewModel(
        factory = ExplainViewModel.factory(sourceThreadId, sourceMessageId),
    )
    val state by viewModel.state.collectAsStateWithLifecycle()
    val context = LocalContext.current

    LaunchedEffect(Unit) {
        viewModel.errors.collect { Toast.makeText(context, it, Toast.LENGTH_LONG).show() }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Explain") },
                navigationIcon = {
                    IconButton(onClick = { navController.popBackStack() }) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                },
            )
        },
        bottomBar = {
            ExplainInputBar(
                question = state.question,
                sending = state.sending,
                onQuestionChange = viewModel::onQuestionChange,
                onAsk = viewModel::ask,
            )
        },
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .background(Slate50)
                .verticalScroll(rememberScrollState())
                .padding(PaddingValues(16.dp)),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            TopCard(args = args)

            if (state.loadingMessages) {
                Box(modifier = Modifier.fillMaxWidth().padding(top = 12.dp), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator(modifier = Modifier.size(20.dp), color = PrimaryBlue)
                }
            } else if (state.messages.isNotEmpty()) {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    state.messages.forEach { msg -> MessageBubble(msg = msg) }
                }
            }
        }
    }
}

@Composable
private fun TopCard(args: ExplainArgsHolder.Args?) {
    Card(
        colors = CardDefaults.cardColors(containerColor = Color.White),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(modifier = Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            SectionLabel("Original message")
            Text(
                args?.messageText ?: "(no message)",
                color = Slate900,
                fontWeight = FontWeight.SemiBold,
                fontSize = 16.sp,
            )
            Spacer(modifier = Modifier.height(8.dp))
            SectionLabel("Correction")
            val correction = args?.correction
            when {
                correction != null -> Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text(correction.corrected, color = Stone900, fontWeight = FontWeight.SemiBold, fontSize = 16.sp)
                    correction.notes.forEach { note ->
                        Text("\u2022 $note", color = Stone700, fontSize = 14.sp)
                    }
                }
                args == null -> Text("Correction was not available.", color = Slate500, fontSize = 14.sp)
                else -> Text("No correction needed.", color = Slate500, fontSize = 14.sp)
            }
        }
    }
}

@Composable
private fun SectionLabel(text: String) {
    Text(
        text.uppercase(),
        color = Slate500,
        fontWeight = FontWeight.Bold,
        fontSize = 11.sp,
        letterSpacing = 0.5.sp,
    )
}

@Composable
private fun MessageBubble(msg: MessageDto) {
    val isAssistant = msg.isAssistant
    val text = if (isAssistant) msg.parseAssistantText() else msg.parseUserContent().text
    Box(modifier = Modifier.fillMaxWidth()) {
        Box(
            modifier = Modifier
                .widthIn(max = 360.dp)
                .align(if (isAssistant) Alignment.CenterStart else Alignment.CenterEnd)
                .then(
                    if (isAssistant) Modifier
                        .background(Color.White, RoundedCornerShape(12.dp))
                        .border(1.dp, Slate200, RoundedCornerShape(12.dp))
                    else Modifier.background(PrimaryBlue, RoundedCornerShape(12.dp)),
                )
                .padding(horizontal = 12.dp, vertical = 10.dp),
        ) {
            Text(
                text = text,
                color = if (isAssistant) Slate900 else Color.White,
                fontSize = 14.sp,
            )
        }
    }
}

@Composable
private fun ExplainInputBar(
    question: String,
    sending: Boolean,
    onQuestionChange: (String) -> Unit,
    onAsk: () -> Unit,
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(Color.White)
            .imePadding()
            .padding(horizontal = 12.dp, vertical = 10.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Text("Ask about this correction", color = Slate500, fontSize = 13.sp, fontWeight = FontWeight.SemiBold)
        Row(verticalAlignment = Alignment.Bottom, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            OutlinedTextField(
                value = question,
                onValueChange = onQuestionChange,
                placeholder = { Text("Why is this corrected that way?") },
                modifier = Modifier
                    .weight(1f)
                    .heightIn(min = 44.dp, max = 120.dp),
                enabled = !sending,
            )
            TextButton(
                onClick = onAsk,
                enabled = !sending && question.isNotBlank(),
                modifier = Modifier
                    .heightIn(min = 44.dp)
                    .background(PrimaryBlue, RoundedCornerShape(10.dp)),
            ) {
                if (sending) CircularProgressIndicator(color = Color.White, modifier = Modifier.size(18.dp))
                else Text("Ask", color = Color.White, fontWeight = FontWeight.Bold)
            }
        }
    }
}
