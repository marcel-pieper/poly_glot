package com.polyglot.android.data.api

import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.PATCH
import retrofit2.http.POST
import retrofit2.http.Path

interface AuthApi {
    @POST("auth/request-code")
    suspend fun requestCode(@Body body: RequestCodeRequest): RequestCodeResponse

    @POST("auth/verify-code")
    suspend fun verifyCode(@Body body: VerifyCodeRequest): VerifyCodeResponse
}

interface MeApi {
    @GET("me")
    suspend fun me(@Header("Authorization") authorization: String): UserDto

    @PATCH("me")
    suspend fun updateMe(
        @Header("Authorization") authorization: String,
        @Body body: UserUpdateRequest,
    ): UserDto

    @DELETE("me")
    suspend fun deleteMe(@Header("Authorization") authorization: String)
}

interface LanguagesApi {
    @GET("languages")
    suspend fun languages(@Header("Authorization") authorization: String): LanguagesResponse
}

interface ChatApi {
    @GET("chat/conversation-starters")
    suspend fun starters(@Header("Authorization") authorization: String): ConversationStartersResponse

    @GET("chat/threads")
    suspend fun threads(@Header("Authorization") authorization: String): ThreadListResponse

    @POST("chat/threads/{id}/generate-title")
    suspend fun generateTitle(
        @Header("Authorization") authorization: String,
        @Path("id") threadId: Long,
    ): GenerateThreadTitleResponse

    @GET("chat/threads/{id}/messages")
    suspend fun messages(
        @Header("Authorization") authorization: String,
        @Path("id") threadId: Long,
    ): MessageListResponse

    @DELETE("chat/threads/{id}")
    suspend fun deleteThread(
        @Header("Authorization") authorization: String,
        @Path("id") threadId: Long,
    )

    @POST("chat/messages")
    suspend fun send(
        @Header("Authorization") authorization: String,
        @Body body: SendMessageRequest,
    ): SendMessageResponse
}

interface ExplainApi {
    @GET("explain/threads/{id}/messages")
    suspend fun messages(
        @Header("Authorization") authorization: String,
        @Path("id") threadId: Long,
    ): MessageListResponse

    @POST("explain/messages")
    suspend fun send(
        @Header("Authorization") authorization: String,
        @Body body: ExplainSendMessageRequest,
    ): SendMessageResponse
}

interface AiApi {
    @POST("ai/translate")
    suspend fun translate(
        @Header("Authorization") authorization: String,
        @Body body: TranslateRequest,
    ): TranslateResponse
}
