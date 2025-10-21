-- Create tables with vote_month columns

-- Users table
CREATE TABLE users (
    user_id BIGSERIAL PRIMARY KEY,
    emp_no VARCHAR(50) NOT NULL UNIQUE,
    emp_nm VARCHAR(100),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_users_emp_no ON users(emp_no);
CREATE INDEX ix_users_user_id ON users(user_id);

-- Menu table
CREATE TABLE menu (
    menu_id BIGSERIAL PRIMARY KEY,
    menu_type VARCHAR(100) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_menu_menu_id ON menu(menu_id);
CREATE INDEX ix_menu_menu_type ON menu(menu_type);

-- Place table
CREATE TABLE place (
    place_id BIGSERIAL PRIMARY KEY,
    place_name VARCHAR(200) NOT NULL,
    address VARCHAR(500),
    latitude FLOAT,
    longitude FLOAT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_place_place_id ON place(place_id);
CREATE INDEX ix_place_place_name ON place(place_name);

-- UserMenuVote table with vote_month
CREATE TABLE user_menu_vote (
    vote_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id),
    menu_id BIGINT NOT NULL REFERENCES menu(menu_id),
    vote_month VARCHAR(6) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_user_menu_vote_user_id ON user_menu_vote(user_id);
CREATE INDEX ix_user_menu_vote_menu_id ON user_menu_vote(menu_id);
CREATE INDEX ix_user_menu_vote_vote_id ON user_menu_vote(vote_id);
CREATE INDEX ix_user_menu_vote_vote_month ON user_menu_vote(vote_month);

-- UserPlaceVote table with vote_month
CREATE TABLE user_place_vote (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id),
    place_id BIGINT NOT NULL REFERENCES place(place_id),
    vote_month VARCHAR(6) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_user_place_vote_id ON user_place_vote(id);
CREATE INDEX ix_user_place_vote_user_id ON user_place_vote(user_id);
CREATE INDEX ix_user_place_vote_place_id ON user_place_vote(place_id);
CREATE INDEX ix_user_place_vote_vote_month ON user_place_vote(vote_month);

-- UserDateVote table with vote_month
CREATE TABLE user_date_vote (
    id BIGSERIAL PRIMARY KEY,
    emp_no VARCHAR(50) NOT NULL,
    preferred_date VARCHAR(20) NOT NULL,
    vote_month VARCHAR(6) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_user_date_vote_id ON user_date_vote(id);
CREATE INDEX ix_user_date_vote_emp_no ON user_date_vote(emp_no);
CREATE INDEX ix_user_date_vote_vote_month ON user_date_vote(vote_month);

-- PlaceVote table with vote_month
CREATE TABLE place_votes (
    id BIGSERIAL PRIMARY KEY,
    place_id BIGINT NOT NULL REFERENCES place(place_id),
    menu_type VARCHAR(100),
    action VARCHAR(20) NOT NULL,
    date VARCHAR(20) NOT NULL,
    vote_month VARCHAR(6) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_place_votes_id ON place_votes(id);
CREATE INDEX ix_place_votes_place_id ON place_votes(place_id);
CREATE INDEX ix_place_votes_vote_month ON place_votes(vote_month);

-- Restaurant suggestions tables
CREATE TABLE restaurant_suggestions (
    id BIGSERIAL PRIMARY KEY,
    emp_no VARCHAR(50) NOT NULL,
    restaurant_name VARCHAR(200) NOT NULL,
    address VARCHAR(500),
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_restaurant_suggestions_id ON restaurant_suggestions(id);
CREATE INDEX ix_restaurant_suggestions_emp_no ON restaurant_suggestions(emp_no);

CREATE TABLE restaurant_suggestion_likes (
    id BIGSERIAL PRIMARY KEY,
    suggestion_id BIGINT NOT NULL REFERENCES restaurant_suggestions(id),
    emp_no VARCHAR(50) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_restaurant_suggestion_likes_id ON restaurant_suggestion_likes(id);
CREATE INDEX ix_restaurant_suggestion_likes_suggestion_id ON restaurant_suggestion_likes(suggestion_id);

CREATE TABLE restaurant_suggestion_comments (
    id BIGSERIAL PRIMARY KEY,
    suggestion_id BIGINT NOT NULL REFERENCES restaurant_suggestions(id),
    emp_no VARCHAR(50) NOT NULL,
    comment TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_restaurant_suggestion_comments_id ON restaurant_suggestion_comments(id);
CREATE INDEX ix_restaurant_suggestion_comments_suggestion_id ON restaurant_suggestion_comments(suggestion_id);

CREATE TABLE restaurant_comment_likes (
    id BIGSERIAL PRIMARY KEY,
    comment_id BIGINT NOT NULL REFERENCES restaurant_suggestion_comments(id),
    emp_no VARCHAR(50) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_restaurant_comment_likes_id ON restaurant_comment_likes(id);
CREATE INDEX ix_restaurant_comment_likes_comment_id ON restaurant_comment_likes(comment_id);
