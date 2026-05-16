package expo.modules.selectionactions

import android.content.Context
import android.graphics.Color
import android.util.TypedValue
import android.view.ActionMode
import android.view.Menu
import android.view.MenuItem
import android.view.View.MeasureSpec
import android.widget.LinearLayout.LayoutParams
import android.widget.TextView
import expo.modules.kotlin.AppContext
import expo.modules.kotlin.viewevent.EventDispatcher
import expo.modules.kotlin.views.ExpoView

/**
 * Selectable assistant text inside React Native Flexbox.
 *
 * Without [shouldUseAndroidLayout] plus [shadowNodeProxy.setViewSize] for intrinsic height,
 * Yoga often measures this view with zero height so only selection handles show.
 */
class SelectableTranslateTextView(context: Context, appContext: AppContext) :
  ExpoView(context, appContext) {

  override val shouldUseAndroidLayout = true

  private val onTranslate by EventDispatcher()

  var translateLabel: String = "Translate"
    set(value) {
      field = value
      textView.invalidate()
    }

  private val textView: TextView = TextView(context).apply {
    setTextIsSelectable(true)
    setTextSize(TypedValue.COMPLEX_UNIT_SP, 15f)
    setTextColor(Color.parseColor("#0f172a"))
    customSelectionActionModeCallback =
      object : ActionMode.Callback {
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
    orientation = VERTICAL
    addView(textView, LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.WRAP_CONTENT))
  }

  override fun onAttachedToWindow() {
    super.onAttachedToWindow()
    post { notifyFabricContentHeightIfPossible() }
  }

  override fun onSizeChanged(w: Int, h: Int, oldw: Int, oldh: Int) {
    super.onSizeChanged(w, h, oldw, oldh)
    if (w != oldw || h != oldh) {
      post { notifyFabricContentHeightIfPossible() }
    }
  }

  override fun onLayout(changed: Boolean, l: Int, t: Int, r: Int, b: Int) {
    super.onLayout(changed, l, t, r, b)
    if (width > 0) {
      post { notifyFabricContentHeightIfPossible() }
    }
  }

  fun applyText(value: String) {
    if (textView.text?.toString() != value) {
      textView.text = value
      invalidateLastReportedSize()
    }
    post { notifyFabricContentHeightIfPossible() }
  }

  fun applyFontSize(sizeSp: Double) {
    textView.setTextSize(TypedValue.COMPLEX_UNIT_SP, sizeSp.toFloat())
    invalidateLastReportedSize()
    post { notifyFabricContentHeightIfPossible() }
  }

  private fun invalidateLastReportedSize() {
    lastReportedWidthDp = -1.0
    lastReportedHeightDp = -1.0
  }

  fun applyColorHex(hex: String?) {
    if (hex.isNullOrBlank()) return
    runCatching { Color.parseColor(hex) }.getOrNull()?.let { textView.setTextColor(it) }
    post { notifyFabricContentHeightIfPossible() }
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

  private var lastReportedWidthDp: Double = -1.0
  private var lastReportedHeightDp: Double = -1.0

  private fun notifyFabricContentHeightIfPossible() {
    if (width <= 0) return
    val density = resources.displayMetrics.density.toDouble()
    textView.measure(
      MeasureSpec.makeMeasureSpec(width, MeasureSpec.EXACTLY),
      MeasureSpec.makeMeasureSpec(0, MeasureSpec.UNSPECIFIED),
    )
    val widthDp = (width.toDouble() / density).coerceAtLeast(0.0)
    val heightDp = (textView.measuredHeight.toDouble() / density).coerceAtLeast(0.0)
    if (widthDp == lastReportedWidthDp && heightDp == lastReportedHeightDp) return
    lastReportedWidthDp = widthDp
    lastReportedHeightDp = heightDp
    // Report finite numbers — NaN is unreliable across the Fabric state bridge.
    shadowNodeProxy.setViewSize(widthDp, heightDp)
  }

  companion object {
    private const val TRANSLATE_ID = 100100
  }
}
