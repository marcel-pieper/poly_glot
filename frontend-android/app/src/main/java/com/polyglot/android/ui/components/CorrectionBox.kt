package com.polyglot.android.ui.components

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.polyglot.android.ui.theme.PrimaryBlue
import com.polyglot.android.ui.theme.Stone700
import com.polyglot.android.ui.theme.Stone900
import com.polyglot.android.ui.theme.Yellow200
import com.polyglot.android.ui.theme.Yellow50
import com.polyglot.android.util.Correction

@Composable
fun CorrectionBox(
    correction: Correction,
    isExpanded: Boolean,
    canOpenExplain: Boolean,
    onToggle: () -> Unit,
    onAsk: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Card(
        colors = CardDefaults.cardColors(containerColor = Yellow50),
        border = BorderStroke(1.dp, Yellow200),
        shape = RoundedCornerShape(10.dp),
        modifier = modifier,
    ) {
        Column(
            modifier = Modifier.padding(10.dp),
            verticalArrangement = Arrangement.spacedBy(4.dp),
        ) {
            Text(
                correction.corrected,
                color = Stone900,
                fontWeight = FontWeight.SemiBold,
                fontSize = 14.sp,
            )
            if (isExpanded) {
                correction.notes.forEach { note ->
                    Text("\u2022 $note", color = Stone700, fontSize = 13.sp)
                }
            }
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.SpaceBetween,
                modifier = Modifier.padding(top = 4.dp).then(Modifier),
            ) {
                Text(
                    text = if (isExpanded) "^" else ">",
                    color = Stone700,
                    fontWeight = FontWeight.Bold,
                    modifier = Modifier.clickable(onClick = onToggle).padding(end = 16.dp),
                )
                if (isExpanded && canOpenExplain) {
                    Text(
                        text = ">> Ask",
                        color = PrimaryBlue,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.SemiBold,
                        textDecoration = TextDecoration.Underline,
                        modifier = Modifier.clickable(onClick = onAsk),
                    )
                }
            }
        }
    }
}
