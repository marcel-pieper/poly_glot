package com.polyglot.android.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.polyglot.android.ui.theme.PrimaryBlue
import com.polyglot.android.ui.theme.Slate300
import com.polyglot.android.ui.theme.Slate900
import com.polyglot.android.ui.theme.SoftBlue

@Composable
fun OptionChip(
    label: String,
    selected: Boolean,
    enabled: Boolean = true,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val border = when {
        selected -> PrimaryBlue
        else -> Slate300
    }
    val bg = if (selected) SoftBlue else Color.White
    val textColor = if (selected) Color(0xFF1E3A8A) else Slate900
    androidx.compose.foundation.layout.Box(
        modifier = modifier
            .alpha(if (enabled) 1f else 0.5f)
            .background(bg, RoundedCornerShape(10.dp))
            .border(1.dp, border, RoundedCornerShape(10.dp))
            .clickable(enabled = enabled, onClick = onClick)
            .padding(horizontal = 10.dp, vertical = 8.dp),
    ) {
        Text(
            text = label,
            color = textColor,
            fontWeight = FontWeight.SemiBold,
            fontSize = 13.sp,
            style = MaterialTheme.typography.labelLarge,
        )
    }
}
