# kotlinx.serialization
-keepattributes *Annotation*, InnerClasses
-dontnote kotlinx.serialization.AnnotationsKt

-keepclassmembers class kotlinx.serialization.json.** {
    *** Companion;
}
-keepclasseswithmembers class kotlinx.serialization.json.** {
    kotlinx.serialization.KSerializer serializer(...);
}

-keep,includedescriptorclasses class com.polyglot.android.**$$serializer { *; }
-keepclassmembers class com.polyglot.android.** {
    *** Companion;
}
-keepclasseswithmembers class com.polyglot.android.** {
    kotlinx.serialization.KSerializer serializer(...);
}

# OkHttp/Retrofit
-dontwarn okhttp3.**
-dontwarn okio.**
-dontwarn retrofit2.**
-keepattributes Signature, Exceptions
