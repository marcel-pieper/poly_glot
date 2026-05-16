package expo.modules.selectionactions

import expo.modules.kotlin.modules.Module
import expo.modules.kotlin.modules.ModuleDefinition

class SelectionActionsModule : Module() {
  override fun definition() = ModuleDefinition {
    Name("SelectionActions")

    View(SelectableTranslateTextView::class) {
      Events("onTranslate")

      Prop("text") { view: SelectableTranslateTextView, value: String ->
        view.applyText(value)
      }

      Prop("fontSize") { view: SelectableTranslateTextView, value: Double? ->
        view.applyFontSize(value ?: 15.0)
      }

      Prop("color") { view: SelectableTranslateTextView, value: String? ->
        view.applyColorHex(value)
      }

      Prop("translateLabel") { view: SelectableTranslateTextView, value: String? ->
        view.translateLabel = value ?: "Translate"
      }
    }
  }
}
