package com.polyglot.android.data.store

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map

private val Context.dataStore by preferencesDataStore(name = "polyglot_auth")

class TokenStore(context: Context) {
    private val ds = context.applicationContext.dataStore

    val tokenFlow: Flow<String?> = ds.data.map { it[KEY] }

    suspend fun get(): String? = tokenFlow.first()

    suspend fun set(token: String) {
        ds.edit { it[KEY] = token }
    }

    suspend fun clear() {
        ds.edit { it.remove(KEY) }
    }

    companion object {
        private val KEY = stringPreferencesKey("polyglot_access_token")
    }
}
