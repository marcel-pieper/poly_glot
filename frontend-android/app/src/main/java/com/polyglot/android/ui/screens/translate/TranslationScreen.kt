package com.polyglot.android.ui.screens.translate

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.navigation.NavHostController
import com.polyglot.android.data.api.userFacingMessage
import com.polyglot.android.di.ServiceLocator
import com.polyglot.android.ui.theme.Red700
import com.polyglot.android.ui.theme.Slate200
import com.polyglot.android.ui.theme.Slate900
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TranslationScreen(navController: NavHostController, inputText: String) {
    val translate = ServiceLocator.translateRepository
    val tokenStore = ServiceLocator.tokenStore
    val scope = rememberCoroutineScope()

    var loading by remember { mutableStateOf(true) }
    var translation by remember { mutableStateOf("") }
    var error by remember { mutableStateOf<String?>(null) }

    fun load() {
        scope.launch {
            loading = true
            error = null
            translation = ""
            val token = tokenStore.get()
            if (token == null) {
                error = "Not authenticated"
                loading = false
                return@launch
            }
            runCatching { translate.translate(token, inputText) }
                .onSuccess { resp ->
                    translation = resp.translatedText
                    if (resp.status != "complete" && resp.translatedText.isBlank()) {
                        error = "Translation failed"
                    }
                }
                .onFailure { err -> error = err.userFacingMessage("Could not translate") }
            loading = false
        }
    }

    LaunchedEffect(inputText) { load() }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Translation") },
                navigationIcon = {
                    IconButton(onClick = { navController.popBackStack() }) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                },
            )
        },
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .padding(PaddingValues(16.dp)),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            Text("Input text", fontWeight = FontWeight.Bold, color = Slate900)
            Card(
                colors = CardDefaults.cardColors(containerColor = Color.White),
                border = androidx.compose.foundation.BorderStroke(1.dp, Slate200),
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text(inputText, modifier = Modifier.padding(14.dp), color = Slate900)
            }

            Text("Translation", fontWeight = FontWeight.Bold, color = Slate900)
            when {
                loading -> CenteredCard {
                    CircularProgressIndicator(modifier = Modifier.padding(bottom = 8.dp))
                    Text("Translating...")
                }
                translation.isNotEmpty() -> Card(
                    colors = CardDefaults.cardColors(containerColor = Color.White),
                    border = androidx.compose.foundation.BorderStroke(1.dp, Slate200),
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Column(modifier = Modifier.padding(14.dp)) {
                        Text(translation, color = Slate900)
                        if (error != null) {
                            Text(error!!, color = Red700, modifier = Modifier.padding(top = 10.dp))
                        }
                    }
                }
                else -> CenteredCard {
                    Text(error ?: "Could not translate", color = Red700)
                    Button(
                        onClick = ::load,
                        modifier = Modifier.padding(top = 6.dp),
                    ) { Text("Retry") }
                }
            }
        }
    }
}

@Composable
private fun CenteredCard(content: @Composable () -> Unit) {
    Card(
        colors = CardDefaults.cardColors(containerColor = Color.White),
        border = androidx.compose.foundation.BorderStroke(1.dp, Slate200),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Box(modifier = Modifier.fillMaxWidth().padding(16.dp), contentAlignment = Alignment.Center) {
            Column(horizontalAlignment = Alignment.CenterHorizontally) { content() }
        }
    }
}
