package expo.modules.selectionactions

import android.content.Context
import android.graphics.Color
import android.util.TypedValue
import android.view.ActionMode
import android.view.Menu
import android.view.MenuItem
import android.widget.TextView
import expo.modules.kotlin.AppContext
import expo.modules.kotlin.viewevent.EventDispatcher
import expo.modules.kotlin.views.ExpoView

class SelectableTranslateTextView(context: Context, appContext: AppContext) : ExpoView(context, appContext) {
  private val onTranslate by EventDispatcher()

  var translateLabel: String = "Translate"
    set(value) {
      field = value
      textView.invalidate()
    }

  private val textView: TextView = TextView(context).apply {
    setTextIsSelectable(true)
    setTextSize(TypedValue.COMPLEX_UNIT_SP, 15f)
    customSelectionActionModeCallback = object : ActionMode.Callback {
      override fun onCreateActionMode(mode: ActionMode, menu: Menu): Boolean {
        menu.add(Menu.NONE, TRANSLATE_ID, Menu.NONE, translateLabel)
        return true
      }

      override fun onPrepareActionMode(mode: ActionMode, menu: Menu): Boolean {
        val existing = menu.findItem(TRANSLATE_ID)
        if (existing == null) {
          menu.add(Menu.NONE, TRANSLATE_ID, Menu.NONE, translateLabel)
        } else {
          existing.title = translateLabel
        }
        return true
      }

      override fun onActionItemClicked(mode: ActionMode, item: MenuItem): Boolean {
        if (item.itemId == TRANSLATE_ID) {
          emitTranslate()
          mode.finish()
          return true
        }
        return false
      }

      override fun onDestroyActionMode(mode: ActionMode) {}
    }
  }

  init {
    addView(textView)
  }

  fun applyText(value: String) {
    if (textView.text?.toString() != value) {
      textView.text = value
    }
  }

  fun applyFontSize(sizeSp: Double) {
    textView.setTextSize(TypedValue.COMPLEX_UNIT_SP, sizeSp.toFloat())
  }

  fun applyColorHex(hex: String?) {
    if (hex.isNullOrBlank()) return
    runCatching { Color.parseColor(hex) }.getOrNull()?.let { textView.setTextColor(it) }
  }

  private fun emitTranslate() {
    val start = textView.selectionStart
    val end = textView.selectionEnd
    val full = textView.text?.toString() ?: ""
    if (start < 0 || end < 0 || start == end) return
    val lo = minOf(start, end)
    val hi = maxOf(start, end).coerceAtMost(full.length)
    val selected = full.substring(lo, hi)
    onTranslate(
      mapOf(
        "text" to selected,
        "fullText" to full,
        "start" to lo,
        "end" to hi,
      )
    )
  }

  companion object {
    private const val TRANSLATE_ID = 100100
  }
}
