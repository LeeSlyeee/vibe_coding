plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.compose)
    alias(libs.plugins.google.services)
}

android {
    namespace = "com.maumon.app"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.maumon.app"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "1.0.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"

        // API Base URL
        buildConfigField("String", "API_BASE_URL", "\"https://217.142.253.35.nip.io/api\"")
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
        debug {
            isDebuggable = true
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }

    // LLM 모델 파일 압축 비활성화 (대용량 .bin)
    androidResources {
        noCompress += "bin"
    }

    packaging {
        jniLibs {
            useLegacyPackaging = true
        }
    }
}

dependencies {
    // Core
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.lifecycle.runtime.ktx)
    implementation(libs.androidx.lifecycle.viewmodel.compose)
    implementation(libs.androidx.activity.compose)

    // Compose
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.ui)
    implementation(libs.androidx.ui.graphics)
    implementation(libs.androidx.ui.tooling.preview)
    implementation(libs.androidx.material3)
    implementation(libs.androidx.material.icons.extended)
    debugImplementation(libs.androidx.ui.tooling)

    // Navigation
    implementation(libs.androidx.navigation.compose)

    // Network (Retrofit + OkHttp)
    implementation(libs.retrofit.core)
    implementation(libs.retrofit.converter.gson)
    implementation(libs.okhttp.logging)

    // Local Storage
    implementation(libs.androidx.datastore.preferences)

    // Coroutines
    implementation(libs.kotlinx.coroutines.android)

    // Image Loading
    implementation(libs.coil.compose)

    // Chart (Vico)
    implementation(libs.vico.compose.m3)

    // On-Device LLM (MediaPipe)
    implementation(libs.mediapipe.tasks.genai)

    // Firebase (Push Notification)
    implementation(platform(libs.firebase.bom))
    implementation(libs.firebase.messaging)

    // Google Play Billing (In-App Subscription)
    implementation(libs.billing)

    // Testing
    testImplementation(libs.junit)
    androidTestImplementation(libs.androidx.junit)
}
