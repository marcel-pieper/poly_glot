package com.polyglot.android.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.IntrinsicSize
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.HelpOutline
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.KeyboardArrowDown
import androidx.compose.material.icons.filled.KeyboardArrowUp
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.polyglot.android.ui.theme.Green600
import com.polyglot.android.ui.theme.Indigo50
import com.polyglot.android.ui.theme.PrimaryBlue
import com.polyglot.android.ui.theme.PrimaryBlueDark
import com.polyglot.android.ui.theme.Red100
import com.polyglot.android.ui.theme.Red700
import com.polyglot.android.ui.theme.Slate200
import com.polyglot.android.ui.theme.Slate500
import com.polyglot.android.ui.theme.Slate600
import com.polyglot.android.ui.theme.Slate700
import com.polyglot.android.ui.theme.Slate900
import com.polyglot.android.util.Correction
import com.polyglot.android.util.TurnStatus
import com.polyglot.android.util.UserContent

private val UserBubbleMaxWidth = 320.dp
private val UserBubbleShape = RoundedCornerShape(topStart = 18.dp, topEnd = 18.dp, bottomStart = 18.dp, bottomEnd = 4.dp)
private val CorrectionCardShape = RoundedCornerShape(12.dp)

@Composable
fun UserMessageRow(
    content: UserContent,
    modifier: Modifier = Modifier,
    isCorrectionExpanded: Boolean = false,
    onToggleCorrection: () -> Unit = {},
    canAskExplain: Boolean = false,
    onAskExplain: () -> Unit = {},
) {
    Column(
        modifier = modifier.fillMaxWidth(),
        horizontalAlignment = Alignment.End,
        verticalArrangement = Arrangement.spacedBy(6.dp),
    ) {
        Box(
            modifier = Modifier
                .widthIn(max = UserBubbleMaxWidth)
                .clip(UserBubbleShape)
                .background(
                    Brush.linearGradient(
                        colors = listOf(PrimaryBlue, PrimaryBlueDark),
                    ),
                )
                .padding(horizontal = 14.dp, vertical = 11.dp),
        ) {
            Text(
                text = content.text,
                color = Color.White,
                fontSize = 15.sp,
                lineHeight = 22.sp,
            )
        }

        when (content.correctionStatus) {
            TurnStatus.Pending -> CorrectionStatusRow(
                modifier = Modifier.widthIn(max = UserBubbleMaxWidth),
            ) {
                CircularProgressIndicator(
                    modifier = Modifier.size(14.dp),
                    strokeWidth = 2.dp,
                    color = PrimaryBlue,
                )
                Text("Checking your message…", color = Slate600, fontSize = 13.sp)
            }

            TurnStatus.Failed -> Box(
                modifier = Modifier
                    .widthIn(max = UserBubbleMaxWidth)
                    .clip(CorrectionCardShape)
                    .background(Red100)
                    .border(1.dp, Slate200, CorrectionCardShape)
                    .padding(horizontal = 12.dp, vertical = 10.dp),
            ) {
                Text(
                    "Could not generate a correction.",
                    color = Red700,
                    fontSize = 13.sp,
                )
            }

            TurnStatus.Complete -> {
                val correction = content.correction
                if (correction != null) {
                    UserCorrectionCard(
                        correction = correction,
                        isExpanded = isCorrectionExpanded,
                        canAskExplain = canAskExplain,
                        onToggle = onToggleCorrection,
                        onAskExplain = onAskExplain,
                        modifier = Modifier.widthIn(max = UserBubbleMaxWidth),
                    )
                } else {
                    Row(
                        modifier = Modifier
                            .clip(RoundedCornerShape(999.dp))
                            .background(Color(0xFFECFDF5))
                            .padding(horizontal = 10.dp, vertical = 5.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(4.dp),
                    ) {
                        Icon(
                            Icons.Default.CheckCircle,
                            contentDescription = null,
                            tint = Green600,
                            modifier = Modifier.size(14.dp),
                        )
                        Text("Looks good", color = Green600, fontSize = 12.sp, fontWeight = FontWeight.Medium)
                    }
                }
            }

            TurnStatus.Unknown -> Unit
        }
    }
}

@Composable
private fun CorrectionStatusRow(
    modifier: Modifier = Modifier,
    content: @Composable () -> Unit,
) {
    Row(
        modifier = modifier
            .clip(CorrectionCardShape)
            .background(Color.White)
            .border(1.dp, Slate200, CorrectionCardShape)
            .padding(horizontal = 12.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        content()
    }
}

@Composable
private fun UserCorrectionCard(
    correction: Correction,
    isExpanded: Boolean,
    canAskExplain: Boolean,
    onToggle: () -> Unit,
    onAskExplain: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Row(
        modifier = modifier
            .height(IntrinsicSize.Min)
            .clip(CorrectionCardShape)
            .background(Color.White)
            .border(1.dp, Slate200, CorrectionCardShape),
    ) {
        Box(
            modifier = Modifier
                .width(4.dp)
                .fillMaxHeight()
                .background(PrimaryBlue),
        )
        Column(
            modifier = Modifier
                .weight(1f)
                .padding(start = 12.dp, end = 12.dp, top = 10.dp, bottom = 10.dp),
            verticalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            Text(
                "SUGGESTED",
                color = Slate500,
                fontSize = 10.sp,
                fontWeight = FontWeight.Bold,
                letterSpacing = 0.8.sp,
            )
            Text(
                correction.corrected,
                color = Slate900,
                fontWeight = FontWeight.SemiBold,
                fontSize = 14.sp,
                lineHeight = 20.sp,
            )
            if (isExpanded && correction.notes.isNotEmpty()) {
                Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    correction.notes.forEach { note ->
                        Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                            Text("•", color = Slate500, fontSize = 13.sp)
                            Text(note, color = Slate700, fontSize = 13.sp, lineHeight = 18.sp)
                        }
                    }
                }
            }
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Row(
                    modifier = Modifier
                        .clip(RoundedCornerShape(8.dp))
                        .clickable(onClick = onToggle)
                        .padding(horizontal = 4.dp, vertical = 2.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(2.dp),
                ) {
                    Text(
                        if (isExpanded) "Less" else "Notes",
                        color = Slate600,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Medium,
                    )
                    Icon(
                        imageVector = if (isExpanded) Icons.Default.KeyboardArrowUp else Icons.Default.KeyboardArrowDown,
                        contentDescription = if (isExpanded) "Collapse notes" else "Expand notes",
                        tint = Slate600,
                        modifier = Modifier.size(18.dp),
                    )
                }
                if (canAskExplain) {
                    Row(
                        modifier = Modifier
                            .clip(RoundedCornerShape(8.dp))
                            .background(Indigo50)
                            .clickable(onClick = onAskExplain)
                            .padding(horizontal = 8.dp, vertical = 4.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(4.dp),
                    ) {
                        Icon(
                            Icons.AutoMirrored.Filled.HelpOutline,
                            contentDescription = null,
                            tint = PrimaryBlue,
                            modifier = Modifier.size(14.dp),
                        )
                        Text(
                            "Ask",
                            color = PrimaryBlue,
                            fontSize = 12.sp,
                            fontWeight = FontWeight.SemiBold,
                        )
                    }
                }
            }
        }
    }
}
