package com.polyglot.android

import android.app.Application
import com.polyglot.android.di.ServiceLocator

class PolyglotApp : Application() {
    override fun onCreate() {
        super.onCreate()
        ServiceLocator.init(this)
    }
}
