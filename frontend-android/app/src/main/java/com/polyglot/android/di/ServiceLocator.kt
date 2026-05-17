package com.polyglot.android.di

import android.content.Context
import retrofit2.converter.kotlinx.serialization.asConverterFactory
import com.polyglot.android.BuildConfig
import com.polyglot.android.data.api.AiApi
import com.polyglot.android.data.api.AuthApi
import com.polyglot.android.data.api.ChatApi
import com.polyglot.android.data.api.ExplainApi
import com.polyglot.android.data.api.LanguagesApi
import com.polyglot.android.data.api.MeApi
import com.polyglot.android.data.repository.AuthRepository
import com.polyglot.android.data.repository.ChatRepository
import com.polyglot.android.data.repository.ExplainRepository
import com.polyglot.android.data.repository.LanguagesRepository
import com.polyglot.android.data.repository.TranslateRepository
import com.polyglot.android.data.store.TokenStore
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import java.util.concurrent.TimeUnit

object ServiceLocator {
    private lateinit var appContext: Context

    private val json: Json by lazy { Json { ignoreUnknownKeys = true; explicitNulls = false } }

    private val okHttp: OkHttpClient by lazy {
        OkHttpClient.Builder()
            .connectTimeout(20, TimeUnit.SECONDS)
            .readTimeout(60, TimeUnit.SECONDS)
            .writeTimeout(60, TimeUnit.SECONDS)
            .apply {
                if (BuildConfig.DEBUG) {
                    addInterceptor(
                        HttpLoggingInterceptor().apply { level = HttpLoggingInterceptor.Level.BASIC },
                    )
                }
            }
            .build()
    }

    private val retrofit: Retrofit by lazy {
        val baseUrl = BuildConfig.API_BASE_URL.let { if (it.endsWith('/')) it else "$it/" }
        Retrofit.Builder()
            .baseUrl(baseUrl)
            .client(okHttp)
            .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
            .build()
    }

    val tokenStore: TokenStore by lazy { TokenStore(appContext) }
    val authApi: AuthApi by lazy { retrofit.create(AuthApi::class.java) }
    val meApi: MeApi by lazy { retrofit.create(MeApi::class.java) }
    val languagesApi: LanguagesApi by lazy { retrofit.create(LanguagesApi::class.java) }
    val chatApi: ChatApi by lazy { retrofit.create(ChatApi::class.java) }
    val explainApi: ExplainApi by lazy { retrofit.create(ExplainApi::class.java) }
    val aiApi: AiApi by lazy { retrofit.create(AiApi::class.java) }

    val authRepository: AuthRepository by lazy { AuthRepository(authApi, meApi, tokenStore) }
    val languagesRepository: LanguagesRepository by lazy { LanguagesRepository(languagesApi, meApi) }
    val chatRepository: ChatRepository by lazy { ChatRepository(chatApi) }
    val explainRepository: ExplainRepository by lazy { ExplainRepository(explainApi) }
    val translateRepository: TranslateRepository by lazy { TranslateRepository(aiApi) }

    fun init(context: Context) {
        appContext = context.applicationContext
        // Trigger AuthRepository init so tokenFlow starts emitting before the UI subscribes.
        authRepository
    }
}
