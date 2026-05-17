package com.polyglot.android.ui.screens.account

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.polyglot.android.ui.components.OptionChip
import com.polyglot.android.ui.theme.Gray500
import com.polyglot.android.ui.theme.Red600
import com.polyglot.android.ui.theme.Slate100

@Composable
fun AccountScreen(viewModel: AccountViewModel = viewModel(factory = AccountViewModel.Factory)) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    var confirmDelete by remember { mutableStateOf(false) }
    val scroll = rememberScrollState()

    Box(
        modifier = Modifier
            .fillMaxSize()
            .padding(top = 0.dp),
    ) {
        Column(
            modifier = Modifier
                .verticalScroll(scroll)
                .padding(PaddingValues(20.dp)),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            Card(
                colors = CardDefaults.cardColors(containerColor = Color.White),
                modifier = Modifier.fillMaxWidth(),
            ) {
                Column(modifier = Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text("Email", color = Gray500, fontSize = 14.sp)
                    Text(
                        state.email,
                        fontSize = 18.sp,
                        fontWeight = FontWeight.SemiBold,
                    )
                }
            }

            LanguageCard(
                title = "Native language",
                currentLabel = state.nativeLanguageLabel,
                options = state.allLanguages,
                selectedId = state.nativeLanguageId,
                isDisabled = { lang -> state.saving || state.activeLanguageId == lang.id },
                onClick = viewModel::setNative,
                helperText = null,
            )

            LanguageCard(
                title = "Active language",
                currentLabel = state.activeLanguageLabel,
                options = state.allLanguages,
                selectedId = state.activeLanguageId,
                isDisabled = { lang ->
                    state.saving || !lang.learningEnabled || state.nativeLanguageId == lang.id
                },
                onClick = viewModel::setActive,
                helperText = "Native and non-learning-enabled languages are disabled.",
            )

            Card(
                colors = CardDefaults.cardColors(containerColor = Color.White),
                modifier = Modifier.fillMaxWidth(),
            ) {
                Column(modifier = Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Button(onClick = viewModel::logout, modifier = Modifier.fillMaxWidth()) {
                        Text("Log out")
                    }
                    Button(
                        onClick = { confirmDelete = true },
                        colors = ButtonDefaults.buttonColors(containerColor = Red600),
                        modifier = Modifier.fillMaxWidth(),
                    ) {
                        Text("Delete account", color = Color.White)
                    }
                }
            }

            state.errorMessage?.let { msg ->
                Text(msg, color = Red600)
            }
        }
    }

    if (confirmDelete) {
        AlertDialog(
            onDismissRequest = { confirmDelete = false },
            title = { Text("Delete account?") },
            text = { Text("This will permanently delete your account and associated data.") },
            confirmButton = {
                TextButton(onClick = {
                    confirmDelete = false
                    viewModel.deleteAccount()
                }) {
                    Text("Delete", color = Red600)
                }
            },
            dismissButton = {
                TextButton(onClick = { confirmDelete = false }) { Text("Cancel") }
            },
        )
    }
}

@Composable
private fun LanguageCard(
    title: String,
    currentLabel: String,
    options: List<com.polyglot.android.data.api.SupportedLanguageDto>,
    selectedId: Long?,
    isDisabled: (com.polyglot.android.data.api.SupportedLanguageDto) -> Boolean,
    onClick: (Long) -> Unit,
    helperText: String?,
) {
    Card(
        colors = CardDefaults.cardColors(containerColor = Color.White),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(
            modifier = Modifier.padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text(title, fontWeight = FontWeight.Bold, fontSize = 16.sp)
            Text(currentLabel, fontSize = 15.sp)
            if (helperText != null) {
                Text(helperText, color = Gray500, fontSize = 13.sp)
            }
            FlowRow(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                options.forEach { lang ->
                    val disabled = isDisabled(lang)
                    OptionChip(
                        label = lang.name,
                        selected = selectedId == lang.id,
                        enabled = !disabled,
                        onClick = { onClick(lang.id) },
                    )
                }
            }
        }
    }
}
