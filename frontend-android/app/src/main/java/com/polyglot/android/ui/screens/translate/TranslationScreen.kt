package com.polyglot.android.ui.screens.translate

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Check
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateMapOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavHostController
import com.polyglot.android.data.api.TranslateItemDto
import com.polyglot.android.data.api.userFacingMessage
import com.polyglot.android.di.ServiceLocator
import com.polyglot.android.ui.theme.PrimaryBlue
import com.polyglot.android.ui.theme.Red700
import com.polyglot.android.ui.theme.Slate200
import com.polyglot.android.ui.theme.Slate500
import com.polyglot.android.ui.theme.Slate900
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TranslationScreen(
    navController: NavHostController,
    inputText: String = "",
    translationId: Long? = null,
) {
    val translate = ServiceLocator.translateRepository
    val vocab = ServiceLocator.vocabRepository
    val tokenStore = ServiceLocator.tokenStore
    val scope = rememberCoroutineScope()
    val viewingSaved = translationId != null && translationId > 0L

    var loading by remember { mutableStateOf(true) }
    var sourceText by remember { mutableStateOf(inputText) }
    var translation by remember { mutableStateOf("") }
    var items by remember { mutableStateOf<List<TranslateItemDto>>(emptyList()) }
    var error by remember { mutableStateOf<String?>(null) }
    val snackbarHostState = remember { SnackbarHostState() }
    val addState = remember { mutableStateMapOf<String, AddVocabUiState>() }

    fun load() {
        scope.launch {
            loading = true
            error = null
            translation = ""
            items = emptyList()
            val token = tokenStore.get()
            if (token == null) {
                error = "Not authenticated"
                loading = false
                return@launch
            }
            if (viewingSaved) {
                runCatching { translate.getTranslation(token, translationId!!) }
                    .onSuccess { resp ->
                        sourceText = resp.sourceText
                        translation = resp.translatedText
                        items = resp.items
                    }
                    .onFailure { err -> error = err.userFacingMessage("Could not load translation") }
            } else {
                sourceText = inputText
                runCatching { translate.translate(token, inputText) }
                    .onSuccess { resp ->
                        translation = resp.translatedText
                        items = resp.items
                        if (resp.status != "complete" && resp.translatedText.isBlank()) {
                            error = "Translation failed"
                        }
                    }
                    .onFailure { err -> error = err.userFacingMessage("Could not translate") }
            }
            loading = false
        }
    }

    LaunchedEffect(inputText, translationId) { load() }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(if (viewingSaved) "Saved translation" else "Translation") },
                navigationIcon = {
                    IconButton(onClick = { navController.popBackStack() }) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                },
            )
        },
        snackbarHost = { SnackbarHost(hostState = snackbarHostState) },
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .padding(PaddingValues(16.dp))
                .verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            Text("Input text", fontWeight = FontWeight.Bold, color = Slate900)
            Card(
                colors = CardDefaults.cardColors(containerColor = Color.White),
                border = androidx.compose.foundation.BorderStroke(1.dp, Slate200),
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text(sourceText, modifier = Modifier.padding(14.dp), color = Slate900)
            }

            Text("Translation", fontWeight = FontWeight.Bold, color = Slate900)
            when {
                loading -> CenteredCard {
                    CircularProgressIndicator(modifier = Modifier.padding(bottom = 8.dp))
                    Text(if (viewingSaved) "Loading..." else "Translating...")
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
                    if (!viewingSaved) {
                        Button(
                            onClick = ::load,
                            modifier = Modifier.padding(top = 6.dp),
                        ) { Text("Retry") }
                    }
                }
            }

            if (items.isNotEmpty()) {
                Text("Items", fontWeight = FontWeight.Bold, color = Slate900)
                items.forEach { item ->
                    val key = vocabKey(item)
                    val rowState = addState[key] ?: AddVocabUiState.Idle
                    ItemRow(
                        item = item,
                        state = rowState,
                        onAddClick = {
                            if (rowState is AddVocabUiState.Loading ||
                                rowState is AddVocabUiState.Added
                            ) return@ItemRow
                            addState[key] = AddVocabUiState.Loading
                            scope.launch {
                                val token = tokenStore.get()
                                if (token == null) {
                                    addState[key] = AddVocabUiState.Idle
                                    snackbarHostState.showSnackbar("Not authenticated")
                                    return@launch
                                }
                                runCatching { vocab.add(token, item.lemma, item.type) }
                                    .onSuccess {
                                        addState[key] = AddVocabUiState.Added
                                    }
                                    .onFailure { err ->
                                        addState[key] = AddVocabUiState.Idle
                                        snackbarHostState.showSnackbar(
                                            err.userFacingMessage("Could not add to vocab"),
                                        )
                                    }
                            }
                        },
                    )
                }
            }
        }
    }
}

private sealed interface AddVocabUiState {
    data object Idle : AddVocabUiState
    data object Loading : AddVocabUiState
    data object Added : AddVocabUiState
}

private fun vocabKey(item: TranslateItemDto): String = "${item.type}::${item.lemma}"

@Composable
private fun ItemRow(
    item: TranslateItemDto,
    state: AddVocabUiState,
    onAddClick: () -> Unit,
) {
    Card(
        colors = CardDefaults.cardColors(containerColor = Color.White),
        border = androidx.compose.foundation.BorderStroke(1.dp, Slate200),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    item.type.uppercase(),
                    color = Slate900,
                    fontSize = 10.sp,
                    fontWeight = FontWeight.SemiBold,
                )
                Text(
                    item.rawItem,
                    color = Slate900,
                    fontWeight = FontWeight.SemiBold,
                    modifier = Modifier.padding(top = 2.dp),
                )
                if (item.rawItemTranslation.isNotBlank()) {
                    Text(
                        item.rawItemTranslation,
                        color = Slate900,
                        fontSize = 13.sp,
                    )
                }
                if (item.lemma.isNotBlank() && item.lemma != item.rawItem) {
                    Text(
                        "lemma: ${item.lemma}",
                        color = Slate900,
                        fontSize = 12.sp,
                        modifier = Modifier.padding(top = 4.dp),
                    )
                }
            }
            when (state) {
                AddVocabUiState.Loading -> Box(
                    modifier = Modifier.size(36.dp),
                    contentAlignment = Alignment.Center,
                ) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(20.dp),
                        strokeWidth = 2.dp,
                    )
                }
                AddVocabUiState.Added -> Box(
                    modifier = Modifier.size(36.dp),
                    contentAlignment = Alignment.Center,
                ) {
                    Icon(
                        Icons.Filled.Check,
                        contentDescription = "Added to vocabulary",
                        tint = PrimaryBlue,
                    )
                }
                AddVocabUiState.Idle -> IconButton(
                    onClick = onAddClick,
                    modifier = Modifier.size(36.dp),
                ) {
                    Icon(
                        Icons.Filled.Add,
                        contentDescription = "Add to vocabulary",
                        tint = Slate500,
                    )
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
