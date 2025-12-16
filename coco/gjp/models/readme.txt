Additional details for the Good Judgment Project data repository.


## Field Details
Many of the field (column) names are common to a range of files in the repository.  Some key value definitions are


```
# IFP identifier
ifp_id        1000-8999       Base number assigned to question


# User identifier
user_id       00001 - 05999 Year 1 GJP
              06000 - 06999 Year 2 GJP
              07000 - 15999 Year 3 GJP
              17500+        Year 4 GJP

# User condition assignment
ctt           
              Individuals
              1a   = Individual w/o training (all years)
              1b   = Individual w/ probability training (all years)
              1c   = Individual w/ scenario training (year 1)
              1h   = Individual w/ training; Hybrid-Accountability (year 4)              
              1n   = MOOF platform with NCBP scoring (year 4)
              1p   = Individual w/ training; Process-Accountability (year 4)
              1r1  = MOOF raters (individuals) (year 4)
              1u   = MOOF platform untrained individuals [no train](year 4) 
              1z   = MOOF platform standard participant (year 4)
              
              Individuals who could see crowd information
              2a   = Crowd information w/o training (year 1) 
              2b   = Crowd information w/ probability training (year 1)
              2c   = Crowd information w/ scenario training (year 1)

              Prediction Markets
              3a   = Lumenogic Prediction Market (year 2)
              3b   = Lumenogic Prediction Market w/ training (year 2)
              3b1  = Lumenogic Prediction Market (year 3) w/ pretty much no training (same market as 3b2)
              3b2  = Lumenogic Prediction Market (year 3) w/ some training (same market as 3b1)
              3e   = Lumenogic Prediction Market for non-citizens / overflow / experimental (year 3)              
              3f   = Inkling Control Prediction Market (year 3 & 4)
              3g1  = Inkling Batch Auction w/o Training (year 4)
              3g2  = Inkling Batch Auction w/ Training (year 4)
              3s   = Inkling Super Market (year 4)
              3txx = Inkling Prediction Market Teams, xx = team_id (year 4)

              Teams (xx = team_id)
              4axx = Teams without training (year 1 & 2)              
              4bxx = Teams with training(all years); Outcome Accountability (year 4)
              4cxx = Teams with scenario training (year 1)
              4dxx = Teams with training and facilitators (year 3)
              4hx  = Teams with training; Hybrid Accountability (year 4)
              4px  = Teams with training; Process Accountability (year 4)
              4uxx = Team size experiment with smaller teams (year 4)
              4wxx = Team size experiment with larger teams (year 4)
              
              Superforecasters (xx = team_id)
              5bxx = Superteams with training (year 2)
              5dxx = Superteams with training and facilitators (year 3)
              5sxx = Superteams with training; Outcome Accountability (year 4)


# forecast identifiers

forecast_id   unique integer identifier within year

fcast_type    0 = new, first forecast on an IFP by a user
              1 = update, subsequent forecast by a user
              2 = affirm, update to a forecast with no change in value
              4 = withdraw (probabilities show last standing, individual scoring stops after this date)

# IFP question type

q_type        0 = regular binomial or multinomial
              1 = cIFP, Answer Option 1 
              2 = cIFP, Answer Option 2
              3 = cIFP, Answer Option 3
              4 = cIFP, Answer Option 4
              5 = cIFP, Answer Option 5
              6 = Ordered Multinomial
              
q_text        Question Text
q_desc        "More Info" and formal resolution criteria

# Current IFP question status
q_status      Voided - not counted for scoring
              Closed - formally resolved and scored


# Other IFP properties              
date_start    YYYY-MM-DD, date question opened for forecasts
date_suspend  YYYY-MM-DD, date question suspended on platforms
date_to_close YYYY-MM-DD, end date as specified in question
date_closed   YYYY-MM-DD HH:MM:SS, date and time question declared closed by MITR
outcome       "a"-"e" as resolved
short_title   main short title


```
