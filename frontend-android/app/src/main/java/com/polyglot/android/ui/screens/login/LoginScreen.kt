package com.polyglot.android.ui.screens.login

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.systemBarsPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.polyglot.android.ui.components.OptionChip
import com.polyglot.android.ui.theme.Indigo50
import com.polyglot.android.ui.theme.PrimaryBlue
import com.polyglot.android.ui.theme.PrimaryBlueDark
import com.polyglot.android.ui.theme.Red100
import com.polyglot.android.ui.theme.Slate800
import com.polyglot.android.ui.theme.SoftBlue

@Composable
fun LoginScreen(viewModel: LoginViewModel = viewModel(factory = LoginViewModel.Factory)) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    val scroll = rememberScrollState()

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Indigo50)
            .systemBarsPadding()
            .imePadding(),
    ) {
        Column(
            modifier = Modifier
                .verticalScroll(scroll)
                .padding(PaddingValues(20.dp)),
            verticalArrangement = Arrangement.spacedBy(0.dp),
        ) {
            Hero()
            Box(modifier = Modifier.height(18.dp))

            when (val step = state.step) {
                LoginStep.Email, LoginStep.Code -> EmailCard(
                    email = state.email,
                    code = state.code,
                    busy = state.busy,
                    devCode = state.devCode,
                    onEmail = viewModel::onEmailChange,
                    onCode = viewModel::onCodeChange,
                    onRequestCode = viewModel::requestCode,
                    onVerify = viewModel::verifyCode,
                )
                LoginStep.NativeLanguage -> {
                    LanguagePickerCard(
                        title = "Choose your native language",
                        subtitle = "Used for corrections and explanations. The active language is excluded.",
                        options = state.nativeOptions,
                        selectedId = state.nativeLanguageId,
                        busy = state.busy,
                        onSelect = viewModel::selectNative,
                        onBack = null,
                    )
                }
                LoginStep.ActiveLanguage -> {
                    LanguagePickerCard(
                        title = "Choose active learning language",
                        subtitle = "Pick the language you are currently learning. Native language is excluded.",
                        options = state.activeOptions,
                        selectedId = state.activeLanguageId,
                        busy = state.busy,
                        onSelect = viewModel::selectActive,
                        onBack = viewModel::goBackToNativeStep,
                    )
                }
            }

            if (state.message.isNotEmpty()) {
                Box(modifier = Modifier.height(14.dp))
                val isError = state.message.contains("failed", ignoreCase = true) ||
                    state.message.contains("invalid", ignoreCase = true)
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(
                            if (isError) Red100 else SoftBlue,
                            RoundedCornerShape(10.dp),
                        )
                        .padding(horizontal = 12.dp, vertical = 10.dp),
                ) {
                    Text(
                        text = state.message,
                        color = Slate800,
                        fontWeight = FontWeight.SemiBold,
                    )
                }
            }
        }
    }
}

@Composable
private fun Hero() {
    Column {
        Box(
            modifier = Modifier
                .size(44.dp)
                .background(PrimaryBlueDark, CircleShape),
            contentAlignment = Alignment.Center,
        ) {
            Text("P", color = Color.White, fontSize = 20.sp, fontWeight = FontWeight.Bold)
        }
        Box(modifier = Modifier.height(14.dp))
        Text(
            "Welcome to Polyglot",
            fontSize = 30.sp,
            fontWeight = FontWeight.ExtraBold,
            color = Color(0xFF111827),
        )
        Box(modifier = Modifier.height(8.dp))
        Text(
            "Log in and quickly set your language preferences.",
            color = Color(0xFF4B5563),
            fontSize = 15.sp,
        )
    }
}

@Composable
private fun EmailCard(
    email: String,
    code: String,
    busy: Boolean,
    devCode: String?,
    onEmail: (String) -> Unit,
    onCode: (String) -> Unit,
    onRequestCode: () -> Unit,
    onVerify: () -> Unit,
) {
    Card(
        colors = CardDefaults.cardColors(containerColor = Color.White),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Text(
                "Email verification login",
                fontWeight = FontWeight.Bold,
                fontSize = 16.sp,
            )
            OutlinedTextField(
                value = email,
                onValueChange = onEmail,
                label = { Text("Email") },
                placeholder = { Text("you@example.com") },
                singleLine = true,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email),
                modifier = Modifier.fillMaxWidth(),
            )
            Button(
                onClick = onRequestCode,
                enabled = !busy,
                colors = ButtonDefaults.buttonColors(containerColor = PrimaryBlue),
                modifier = Modifier.fillMaxWidth(),
            ) {
                if (busy) {
                    CircularProgressIndicator(color = Color.White, modifier = Modifier.size(20.dp))
                } else {
                    Text("Send verification code", fontWeight = FontWeight.Bold)
                }
            }
            OutlinedTextField(
                value = code,
                onValueChange = onCode,
                label = { Text("Verification code") },
                placeholder = { Text("6-digit code") },
                singleLine = true,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                modifier = Modifier.fillMaxWidth(),
            )
            Button(
                onClick = onVerify,
                enabled = !busy,
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF111827)),
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text("Verify and continue", color = Color.White, fontWeight = FontWeight.Bold)
            }
            if (!devCode.isNullOrEmpty()) {
                Text(
                    "Dev code: $devCode",
                    color = PrimaryBlueDark,
                    fontWeight = FontWeight.Bold,
                )
            }
        }
    }
}

@Composable
private fun LanguagePickerCard(
    title: String,
    subtitle: String,
    options: List<LoginLanguageOption>,
    selectedId: Long?,
    busy: Boolean,
    onSelect: (Long) -> Unit,
    onBack: (() -> Unit)?,
) {
    Card(
        colors = CardDefaults.cardColors(containerColor = Color.White),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Text(title, fontWeight = FontWeight.Bold, fontSize = 16.sp)
            Text(subtitle, color = Color(0xFF4B5563), fontSize = 14.sp)
            androidx.compose.foundation.layout.FlowRow(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                options.forEach { opt ->
                    OptionChip(
                        label = opt.name,
                        selected = selectedId == opt.id,
                        enabled = !busy,
                        onClick = { onSelect(opt.id) },
                    )
                }
            }
            if (onBack != null) {
                androidx.compose.material3.TextButton(onClick = onBack) {
                    Text("Back", color = PrimaryBlueDark, fontWeight = FontWeight.Bold)
                }
            }
        }
    }
}
