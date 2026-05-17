package com.polyglot.android.ui.components

import android.util.TypedValue
import android.view.ActionMode
import android.view.Menu
import android.view.MenuItem
import android.widget.TextView
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.unit.TextUnit
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView

/**
 * Selectable text that injects a custom "Translate" item into the system selection ActionMode.
 *
 * This is the native equivalent of the old Expo `SelectableTranslateTextView` Fabric module.
 * No shadow nodes, no measure-and-report — `TextView` does what it has always done.
 */
@Composable
fun SelectableTranslatableText(
    text: String,
    onTranslate: (String) -> Unit,
    modifier: Modifier = Modifier,
    fontSize: TextUnit = 15.sp,
    color: Color = Color(0xFF0F172A),
    translateLabel: String = "Translate",
) {
    // Keep latest callback so the ActionMode doesn't capture a stale lambda.
    val callbackRef = remember { CallbackRef() }
    callbackRef.onTranslate = onTranslate
    callbackRef.label = translateLabel

    AndroidView(
        modifier = modifier,
        factory = { ctx ->
            TextView(ctx).apply {
                setTextIsSelectable(true)
                customSelectionActionModeCallback = object : ActionMode.Callback {
                    override fun onCreateActionMode(mode: ActionMode, menu: Menu): Boolean {
                        menu.add(Menu.NONE, MENU_TRANSLATE, Menu.NONE, callbackRef.label)
                        return true
                    }

                    override fun onPrepareActionMode(mode: ActionMode, menu: Menu): Boolean {
                        val existing = menu.findItem(MENU_TRANSLATE)
                        if (existing == null) {
                            menu.add(Menu.NONE, MENU_TRANSLATE, Menu.NONE, callbackRef.label)
                        } else {
                            existing.title = callbackRef.label
                        }
                        return true
                    }

                    override fun onActionItemClicked(mode: ActionMode, item: MenuItem): Boolean {
                        if (item.itemId != MENU_TRANSLATE) return false
                        val full = this@apply.text?.toString().orEmpty()
                        val s = selectionStart.coerceAtLeast(0)
                        val e = selectionEnd.coerceAtLeast(0)
                        if (s != e) {
                            val lo = minOf(s, e)
                            val hi = maxOf(s, e).coerceAtMost(full.length)
                            val selected = full.substring(lo, hi).trim()
                            if (selected.isNotEmpty()) callbackRef.onTranslate(selected)
                        }
                        mode.finish()
                        return true
                    }

                    override fun onDestroyActionMode(mode: ActionMode) {}
                }
            }
        },
        update = { tv ->
            if (tv.text?.toString() != text) tv.text = text
            tv.setTextSize(TypedValue.COMPLEX_UNIT_SP, fontSize.value)
            tv.setTextColor(color.toArgb())
        },
    )
}

private const val MENU_TRANSLATE = 100100

private class CallbackRef {
    var onTranslate: (String) -> Unit = {}
    var label: String = "Translate"
}
