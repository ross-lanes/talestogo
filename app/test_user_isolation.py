#!/usr/bin/env python3
"""
User Isolation Verification Test

This script tests that user data is properly isolated and no data leakage occurs.

Tests:
1. New users start with empty data (no queries, descriptors, competitors)
2. Users cannot see other users' data
3. All CRUD operations properly filter by user_id
4. Brand switching properly filters data by brand_id

Usage:
    python test_user_isolation.py
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import app modules as a package
parent_dir = str(Path(__file__).parent.parent)
sys.path.insert(0, parent_dir)

from app.database import SessionLocal, engine
from app import models, crud, schemas
from sqlalchemy.orm import Session

def test_empty_user_data(db: Session, user_id: int):
    """Test that a user starts with empty data."""
    print("\n" + "="*60)
    print("TEST 1: New user should have empty data")
    print("="*60)

    # Test queries
    queries = crud.get_queries(db, user_id=user_id, brand_id=None)
    print(f"Queries: {len(queries)} (expected: 0)")
    assert len(queries) == 0, f"Expected 0 queries, found {len(queries)}"

    # Test descriptors
    descriptors = crud.get_descriptors(db, user_id=user_id, brand_id=None)
    print(f"Descriptors: {len(descriptors)} (expected: 0)")
    assert len(descriptors) == 0, f"Expected 0 descriptors, found {len(descriptors)}"

    # Test competitors
    competitors = crud.get_competitors(db, user_id=user_id, brand_id=None)
    print(f"Competitors: {len(competitors)} (expected: 0)")
    assert len(competitors) == 0, f"Expected 0 competitors, found {len(competitors)}"

    # Test responses
    responses = crud.get_responses(db, user_id=user_id, brand_id=None)
    print(f"Responses: {len(responses)} (expected: 0)")
    assert len(responses) == 0, f"Expected 0 responses, found {len(responses)}"

    # Test brands
    brands = crud.get_all_brands(db, user_id=user_id)
    print(f"Brands: {len(brands)} (expected: 0)")
    assert len(brands) == 0, f"Expected 0 brands, found {len(brands)}"

    print("✓ TEST PASSED: User has no data")

def test_user_data_isolation(db: Session, user1_id: int, user2_id: int):
    """Test that users cannot see each other's data."""
    print("\n" + "="*60)
    print("TEST 2: User data isolation")
    print("="*60)

    # Create test data for user 1
    query1 = schemas.QueryCreate(
        query_id="TEST001",
        query_text="User 1's test query",
        category="Test",
        priority="High",
        active=True
    )
    created_query1 = crud.create_query(db, query=query1, user_id=user1_id, brand_id=None)
    print(f"Created query for user {user1_id}: {created_query1.query_text}")

    # Create test data for user 2
    query2 = schemas.QueryCreate(
        query_id="TEST002",
        query_text="User 2's test query",
        category="Test",
        priority="High",
        active=True
    )
    created_query2 = crud.create_query(db, query=query2, user_id=user2_id, brand_id=None)
    print(f"Created query for user {user2_id}: {created_query2.query_text}")

    # User 1 should only see their own query
    user1_queries = crud.get_queries(db, user_id=user1_id, brand_id=None)
    print(f"User {user1_id} sees {len(user1_queries)} queries")
    assert len(user1_queries) == 1, f"User 1 should see 1 query, saw {len(user1_queries)}"
    assert user1_queries[0].query_text == "User 1's test query"

    # User 2 should only see their own query
    user2_queries = crud.get_queries(db, user_id=user2_id, brand_id=None)
    print(f"User {user2_id} sees {len(user2_queries)} queries")
    assert len(user2_queries) == 1, f"User 2 should see 1 query, saw {len(user2_queries)}"
    assert user2_queries[0].query_text == "User 2's test query"

    # Clean up
    db.delete(created_query1)
    db.delete(created_query2)
    db.commit()

    print("✓ TEST PASSED: Users can only see their own data")

def test_brand_data_isolation(db: Session, user_id: int):
    """Test that brand data is properly isolated."""
    print("\n" + "="*60)
    print("TEST 3: Brand data isolation")
    print("="*60)

    # Create two brands for the user
    brand1 = schemas.BrandInfoCreate(
        brand_name="Brand A",
        website_url="https://brand-a.com",
        industry="Technology",
        is_active=True
    )
    created_brand1 = crud.create_brand_info(db, brand_info=brand1, user_id=user_id)
    print(f"Created Brand A (id={created_brand1.id})")

    brand2 = schemas.BrandInfoCreate(
        brand_name="Brand B",
        website_url="https://brand-b.com",
        industry="Healthcare",
        is_active=False
    )
    created_brand2 = crud.create_brand_info(db, brand_info=brand2, user_id=user_id)
    print(f"Created Brand B (id={created_brand2.id})")

    # Create queries for each brand
    query_a = schemas.QueryCreate(
        query_id="BA001",
        query_text="Brand A query",
        category="Test",
        priority="High",
        active=True
    )
    created_query_a = crud.create_query(db, query=query_a, user_id=user_id, brand_id=created_brand1.id)

    query_b = schemas.QueryCreate(
        query_id="BB001",
        query_text="Brand B query",
        category="Test",
        priority="High",
        active=True
    )
    created_query_b = crud.create_query(db, query=query_b, user_id=user_id, brand_id=created_brand2.id)

    # Get queries for brand A only
    brand_a_queries = crud.get_queries(db, user_id=user_id, brand_id=created_brand1.id)
    print(f"Brand A queries: {len(brand_a_queries)} (expected: 1)")
    assert len(brand_a_queries) == 1, f"Should see 1 Brand A query, saw {len(brand_a_queries)}"
    assert brand_a_queries[0].query_text == "Brand A query"

    # Get queries for brand B only
    brand_b_queries = crud.get_queries(db, user_id=user_id, brand_id=created_brand2.id)
    print(f"Brand B queries: {len(brand_b_queries)} (expected: 1)")
    assert len(brand_b_queries) == 1, f"Should see 1 Brand B query, saw {len(brand_b_queries)}"
    assert brand_b_queries[0].query_text == "Brand B query"

    # Get all queries (no brand filter)
    all_queries = crud.get_queries(db, user_id=user_id, brand_id=None)
    print(f"All queries: {len(all_queries)} (expected: 2)")
    assert len(all_queries) == 2, f"Should see 2 total queries, saw {len(all_queries)}"

    # Clean up
    db.delete(created_query_a)
    db.delete(created_query_b)
    db.delete(created_brand1)
    db.delete(created_brand2)
    db.commit()

    print("✓ TEST PASSED: Brand data is properly isolated")

def test_no_orphaned_data(db: Session):
    """Test that there are no orphaned records in the database."""
    print("\n" + "="*60)
    print("TEST 4: No orphaned data (NULL user_id)")
    print("="*60)

    tables_to_check = [
        ('queries', models.Query),
        ('responses', models.Response),
        ('competitors', models.Competitor),
        ('target_descriptors', models.TargetDescriptor),
        ('campaigns', models.Campaign),
        ('cited_sources', models.CitedSource),
        ('reports', models.Report),
        ('task_status', models.TaskStatus),
        ('trends', models.Trend),
        ('analyses', models.AnalysisHistory),
    ]

    all_clean = True
    for table_name, model_class in tables_to_check:
        orphaned = db.query(model_class).filter(model_class.user_id == None).count()
        if orphaned > 0:
            print(f"✗ {table_name}: {orphaned} orphaned records found")
            all_clean = False
        else:
            print(f"✓ {table_name}: No orphaned records")

    assert all_clean, "Found orphaned records in database!"
    print("✓ TEST PASSED: No orphaned data found")

def main():
    """Run all user isolation tests."""
    print("="*60)
    print("USER ISOLATION VERIFICATION TESTS")
    print("="*60)

    # Create database session
    db = SessionLocal()

    try:
        # Get or create test users
        test_user1 = db.query(models.User).filter(models.User.email == "test_user_1@example.com").first()
        if not test_user1:
            test_user1 = models.User(
                email="test_user_1@example.com",
                full_name="Test User 1",
                is_active=True,
                is_admin=False
            )
            db.add(test_user1)
            db.commit()
            db.refresh(test_user1)
            print(f"Created test user 1 (id={test_user1.id})")
        else:
            print(f"Using existing test user 1 (id={test_user1.id})")

        test_user2 = db.query(models.User).filter(models.User.email == "test_user_2@example.com").first()
        if not test_user2:
            test_user2 = models.User(
                email="test_user_2@example.com",
                full_name="Test User 2",
                is_active=True,
                is_admin=False
            )
            db.add(test_user2)
            db.commit()
            db.refresh(test_user2)
            print(f"Created test user 2 (id={test_user2.id})")
        else:
            print(f"Using existing test user 2 (id={test_user2.id})")

        # Run tests
        test_no_orphaned_data(db)
        test_empty_user_data(db, user_id=test_user1.id)
        test_user_data_isolation(db, user1_id=test_user1.id, user2_id=test_user2.id)
        test_brand_data_isolation(db, user_id=test_user1.id)

        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED!")
        print("="*60)
        print("\nUser isolation is working correctly:")
        print("  ✓ No orphaned data in database")
        print("  ✓ New users start with empty data")
        print("  ✓ Users cannot see each other's data")
        print("  ✓ Brand data is properly isolated")

        return 0

    except AssertionError as e:
        print("\n" + "="*60)
        print(f"✗ TEST FAILED: {e}")
        print("="*60)
        return 1

    except Exception as e:
        print("\n" + "="*60)
        print(f"✗ ERROR: {e}")
        print("="*60)
        import traceback
        traceback.print_exc()
        return 1

    finally:
        db.close()

if __name__ == "__main__":
    sys.exit(main())
