const admin = require('firebase-admin');

// Firebase Admin SDK 초기화 (Application Default Credentials 사용)
admin.initializeApp({
  projectId: 'ecb-human-survey'
});

const db = admin.firestore();

async function exportAMTEvaluations() {
  console.log('=== AMT 평가 데이터 Export 시작 ===');

  try {
    // amt_evaluations 컬렉션에서 모든 문서 가져오기
    const snapshot = await db.collection('amt_evaluations').get();

    if (snapshot.empty) {
      console.log('❌ amt_evaluations 컬렉션에 데이터가 없습니다.');
      return {};
    }

    const data = {};
    snapshot.forEach(doc => {
      data[doc.id] = doc.data();
      console.log(`✅ ${doc.id} 데이터 추출됨`);
    });

    console.log(`\\n📊 총 ${Object.keys(data).length}개 문서 추출됨`);

    // JSON 파일로 저장
    const fs = require('fs');
    fs.writeFileSync('../firebase_amt_export.json', JSON.stringify(data, null, 2));
    console.log('💾 firebase_amt_export.json 파일로 저장됨');

    return data;

  } catch (error) {
    console.error('❌ 데이터 export 실패:', error);
    throw error;
  }
}

// 실행
exportAMTEvaluations()
  .then(() => {
    console.log('\\n🎉 Export 완료!');
    process.exit(0);
  })
  .catch(error => {
    console.error('\\n💥 Export 실패:', error);
    process.exit(1);
  });