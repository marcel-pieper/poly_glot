package com.polyglot.android.ui.screens.home

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.Chat
import androidx.compose.material.icons.automirrored.outlined.Chat
import androidx.compose.material.icons.filled.AccountCircle
import androidx.compose.material.icons.filled.FitnessCenter
import androidx.compose.material.icons.filled.MenuBook
import androidx.compose.material.icons.filled.Translate
import androidx.compose.material.icons.outlined.AccountCircle
import androidx.compose.material.icons.outlined.FitnessCenter
import androidx.compose.material.icons.outlined.MenuBook
import androidx.compose.material.icons.outlined.Translate
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavHostController
import com.polyglot.android.ui.screens.account.AccountScreen
import com.polyglot.android.ui.screens.chat.ChatOverviewScreen
import com.polyglot.android.ui.screens.translate.TranslateOverviewScreen
import com.polyglot.android.ui.theme.Slate500
import com.polyglot.android.ui.theme.Slate900

private enum class HomeTab(val title: String) {
    Practice("Practice"),
    Vocab("Vocab"),
    Chat("Chat"),
    Translate("Translate"),
    Data("Data"),
}

@Composable
fun HomeTabsScreen(navController: NavHostController) {
    var current by rememberSaveable { mutableStateOf(HomeTab.Chat) }

    Scaffold(
        bottomBar = {
            NavigationBar {
                HomeTab.entries.forEach { tab ->
                    val selected = tab == current
                    NavigationBarItem(
                        selected = selected,
                        onClick = { current = tab },
                        icon = { TabIcon(tab, selected) },
                        label = { Text(tab.title, fontSize = 12.sp) },
                    )
                }
            }
        },
    ) { innerPadding ->
        Box(modifier = Modifier.fillMaxSize().padding(innerPadding)) {
            when (current) {
                HomeTab.Practice -> Placeholder("Practice")
                HomeTab.Vocab -> Placeholder("Vocab")
                HomeTab.Chat -> ChatOverviewScreen(navController = navController)
                HomeTab.Translate -> TranslateOverviewScreen(navController = navController)
                HomeTab.Data -> AccountScreen()
            }
        }
    }
}

@Composable
private fun TabIcon(tab: HomeTab, selected: Boolean) {
    val (filled, outlined, desc) = when (tab) {
        HomeTab.Practice -> Triple(Icons.Filled.FitnessCenter, Icons.Outlined.FitnessCenter, "Practice")
        HomeTab.Vocab -> Triple(Icons.Filled.MenuBook, Icons.Outlined.MenuBook, "Vocab")
        HomeTab.Chat -> Triple(Icons.AutoMirrored.Filled.Chat, Icons.AutoMirrored.Outlined.Chat, "Chat")
        HomeTab.Translate -> Triple(Icons.Filled.Translate, Icons.Outlined.Translate, "Translate")
        HomeTab.Data -> Triple(Icons.Filled.AccountCircle, Icons.Outlined.AccountCircle, "Data")
    }
    Icon(imageVector = if (selected) filled else outlined, contentDescription = desc)
}

@Composable
private fun Placeholder(title: String) {
    Column(
        modifier = Modifier.fillMaxSize(),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text(title, fontSize = 30.sp, fontWeight = FontWeight.Bold, color = Slate900)
        Text("Placeholder page", color = Slate500, fontSize = 15.sp)
    }
}
