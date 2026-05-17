package com.polyglot.android.ui.screens.translate

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.defaultMinSize
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavHostController
import com.polyglot.android.ui.nav.Routes
import com.polyglot.android.ui.theme.PrimaryBlue
import com.polyglot.android.ui.theme.Slate500
import com.polyglot.android.ui.theme.Slate900

@Composable
fun TranslateOverviewScreen(navController: NavHostController) {
    var input by rememberSaveable { mutableStateOf("") }
    var history by rememberSaveable { mutableStateOf(listOf<String>()) }
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
                history = listOf(v) + history
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

        Box(modifier = Modifier.height(4.dp))
        Text("Previous translations", fontSize = 16.sp, fontWeight = FontWeight.Bold, color = Slate900)

        if (history.isEmpty()) {
            Card(
                colors = CardDefaults.cardColors(containerColor = Color.White),
                modifier = Modifier.fillMaxWidth(),
            ) {
                Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text("No translations yet", fontWeight = FontWeight.Bold, color = Slate900)
                    Text(
                        "Your previous translation requests will appear here.",
                        color = Slate500,
                        fontSize = 13.sp,
                    )
                }
            }
        } else {
            LazyColumn(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                items(history) { item ->
                    Card(
                        colors = CardDefaults.cardColors(containerColor = Color.White),
                        modifier = Modifier.fillMaxWidth(),
                    ) {
                        Text(item, modifier = Modifier.padding(14.dp), color = Slate900, fontSize = 15.sp)
                    }
                }
            }
        }
    }
}
