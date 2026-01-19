/**
 * Initialize Task Slots for Race-Condition-Free Task Assignment
 *
 * Creates 30 slot documents (10 tasks × 3 slots) in the `amt_task_slots` collection.
 * Each slot can be atomically claimed by one user using Firestore transactions.
 *
 * Usage:
 *   cd survey && node scripts/init_task_slots.js
 *
 * Prerequisites:
 *   - Firebase Admin SDK configured (gcloud auth application-default login)
 *   - Or set GOOGLE_APPLICATION_CREDENTIALS environment variable
 */

const admin = require('firebase-admin');

// Firebase Admin SDK initialization (using Application Default Credentials)
admin.initializeApp({
  projectId: 'ecb-human-survey'
});

const db = admin.firestore();

const TOTAL_TASKS = 10;
const SLOTS_PER_TASK = 3;

async function initTaskSlots() {
  console.log('=== Initializing Task Slots ===\n');

  try {
    // Check if slots already exist
    const existingSlots = await db.collection('amt_task_slots').limit(1).get();

    if (!existingSlots.empty) {
      console.log('⚠️  amt_task_slots collection already has data.');
      console.log('   Use --force flag to reinitialize (WARNING: this will reset all slots)\n');

      // Show current state
      const allSlots = await db.collection('amt_task_slots').get();
      const stats = { available: 0, in_progress: 0, completed: 0 };
      allSlots.forEach(doc => {
        const data = doc.data();
        stats[data.status] = (stats[data.status] || 0) + 1;
      });
      console.log('Current slot status:');
      console.log(`  - Available: ${stats.available}`);
      console.log(`  - In Progress: ${stats.in_progress}`);
      console.log(`  - Completed: ${stats.completed}`);

      if (!process.argv.includes('--force')) {
        process.exit(0);
      }
      console.log('\n--force flag detected. Reinitializing all slots...\n');
    }

    // Use batched writes for atomicity
    const batch = db.batch();
    let slotCount = 0;

    for (let taskId = 1; taskId <= TOTAL_TASKS; taskId++) {
      for (let slotNum = 1; slotNum <= SLOTS_PER_TASK; slotNum++) {
        const docId = `task_${taskId}_slot_${slotNum}`;
        const docRef = db.collection('amt_task_slots').doc(docId);

        batch.set(docRef, {
          taskId: taskId,
          slotNum: slotNum,
          claimedBy: null,        // null = available, string = user UID
          claimedAt: null,        // Timestamp when claimed
          status: 'available'     // 'available' | 'in_progress' | 'completed'
        });

        slotCount++;
      }
    }

    await batch.commit();
    console.log(`✅ Created ${slotCount} task slots (${TOTAL_TASKS} tasks × ${SLOTS_PER_TASK} slots)\n`);

    // Verify creation
    const verifySnapshot = await db.collection('amt_task_slots').get();
    console.log(`📊 Verification: ${verifySnapshot.size} documents in amt_task_slots\n`);

    // Print slot summary
    console.log('Slot Structure:');
    console.log('┌──────────┬────────┬───────────┬───────────┬──────────┐');
    console.log('│ Task ID  │ Slot # │ Status    │ ClaimedBy │ ClaimedAt│');
    console.log('├──────────┼────────┼───────────┼───────────┼──────────┤');

    for (let taskId = 1; taskId <= Math.min(3, TOTAL_TASKS); taskId++) {
      for (let slotNum = 1; slotNum <= SLOTS_PER_TASK; slotNum++) {
        const docId = `task_${taskId}_slot_${slotNum}`;
        const doc = await db.collection('amt_task_slots').doc(docId).get();
        const data = doc.data();
        console.log(`│ ${String(taskId).padStart(8)} │ ${String(slotNum).padStart(6)} │ ${data.status.padEnd(9)} │ ${(data.claimedBy || '-').slice(0, 9).padEnd(9)} │ ${(data.claimedAt || '-').toString().slice(0, 8).padEnd(8)} │`);
      }
    }
    if (TOTAL_TASKS > 3) {
      console.log('│   ...    │  ...   │    ...    │    ...    │   ...    │');
    }
    console.log('└──────────┴────────┴───────────┴───────────┴──────────┘');

    console.log('\n✨ Initialization complete!');
    console.log('\nNext steps:');
    console.log('1. Verify in Firebase Console: https://console.firebase.google.com');
    console.log('2. Test slot claiming with concurrent requests');
    console.log('3. Monitor amt_task_slots collection during survey\n');

  } catch (error) {
    console.error('❌ Initialization failed:', error);
    throw error;
  }
}

// Run the script
initTaskSlots()
  .then(() => {
    console.log('🎉 Done!');
    process.exit(0);
  })
  .catch(error => {
    console.error('💥 Script failed:', error);
    process.exit(1);
  });
