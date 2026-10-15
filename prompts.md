# Prompts used to build this project

User-authored project prompts from this conversation, in chronological order. Automatic browser/environment context and tool outputs are omitted. Whitespace and incidental formatting are normalized; wording is otherwise preserved. Assistant responses are not included.

## 1. Create the repository

create an emtpy repo called pinwheel-take-home and push to remote

## 2. Retry authentication

logged in now, pls retry

## 3. Locate the project

where is this project locally?

## 4. Move the project

can you move it to /Users/dianelin/Documents/ChatGPT

## 5. Understand the source data

walk me through the adp_ner_history.csv file taht I pulled from this site: https://adpemploymentreport.com/

tell me about the shape, granularity, and contents of the data

## 6. Build an exploratory dashboard

create a UI where a user can view this information. users should be able to check/uncheck categories (represented as distinct lines in a graph), filter for a particular date range, etc. run it locally so i can play around with it

## 7. Assignment and forecasting plan

here's the problme statement for the assignment:

### The Problem

Build a small command-line tool that tracks the monthly [ADP National Employment Report](https://adpemploymentreport.com/) and forecasts the next set of numbers (i.e. the next print of numbers). A user should be able to:

- See historical numbers
- See your prediction for next month
- Understand *why* you predicted what you did

A CLI is the default and entirely sufficient. A web UI is optional. We’re more interested in system design and problem composition.

You decide everything else — what data to pull, how sophisticated the forecast is, how the pieces fit together. **How you measure the accuracy of your forecasts is also your call** — pick an approach, justify it, and show your work.

There is no hidden requirements list. We care more about how you structure the code and defend your choices than about the sophistication of any single component. **We’re evaluating your ability to build with AI, you should show off as best you can**.

what are your thoughts on the best way to forecast this data? I'm specifically curious about

- all the different ways we can forecast the next month's worth of data
- which methodology is right for the assignment
- what pieces of the supplied data can we leave out of hte forecaster (ie, should we leave out weekly data because the monthly data is what's required? or shoudl we use the weekly data because it gives us better granularity which is more useful for mkaing predictions?)

let's nail down a game plan for the forecasting logic before adding to the codebase.

## 8. Choose exponential smoothing and historical testing

we don't' have the luxury of waiting multiple months to see if our prediction is accurate. we need to create this forecaster today with a reasonable justification for why we picked the forecasting model we picked.

also i think that whichever model we pick, we should use historical data to do the testing.

my suggestion is to use exponential smoothing: Average past changes, giving recent months more weight. i also think there's a way to incoporate seasonality (ie, what if sept is a big growth month YOY?)

## 9. Implement the forecasting backend

okay fair point - let's not overindex on the seasonality bit. let's just use simple exponential smoothing. i think it's fair to not count the pandemic when doing accuracy testing

the scope you listed out makes sense. the limitation of revised history in the csv is fine.

let's proceed with first

- implementing a forecasting class. in the backend we should have the exponential smoothing model.
- for now we can use the csv in the root directory but a future iteration is that we should pull directly from the adp website for the latest data

## 10. Display forecasts

in the dashboard, add the predicted next month with some sort of visual indicator that it is the next predicted month. also include some explanation as to how we made this forecast

## 11. Dashboard layout and forecast styling

couple of ui tweaks:

- remove the header (pinewheel/data explorer / adp employement data)
- put the categories on the right hand side and the drop down selectors in their place
- remove the selectors for frequency and adjustment and just keep them at monthly / seasonally adjust so that the forecast is always visible
- have a vertical grey bar to denote the prediction in addition to the dotted line
- put the predicted change in green or red depending on increase or decrease

## 12. Simplify the dashboard

additional tweaks:

- remove the "indexed growth" option from the View dropdown
- change the default view to be the last 5 years rather than since jan 1 2020
- remove "last 5 years" from quick range and replace wiht YTD
- put the categories on the left hand side, at the very bottom of the the dropdowns. put breakdown dropdown right above it
- remove the longer explanation from the purple box in the ui "Simple exponential smoothing of 200 monthly seasonally adjusted changes,...". right after "he chart extends one month beyond the latest observation." add this: "The forecast was calculated using exponential smoothing from the previous 200 monthly seasonally adjusted changes. Each update gives the newest change 30% weight and the previous smoothed estimate 70%. "

## 13. Write the README

add a readme with the following sections:

- How to run the project (another user should be able to clone the repo and run regardless of local setup. if current configuration using python runserver isn't sufficient for this requiremnet, suggest something that is)
- Approach and Key Tradeoffs (here we can discuss a few options we considered and why we went with the exponential smoothing, why we discarded weekly data, etc)
- How you evaluated forecast accuracy and what the results were (leave this seciton blank for now)
- What you'd build next if you had another week

## 14. Clarify runtime requirements

a user has to have python 3.10 installed in order to run this locally?

## 15. Question the smoothing weight

why did we select 0.3 ?

## 16. Test a historical forecast

let's talk about testing. using our forecastiing model, how accurate are our predictions?

for example, let's train our model up until the end of 2025. how accurate did it predict jan 2026's employment levels?

## 17. Graph historical accuracy

can we get a graph of accuracy month over month for all months, excluding the pandemic months? important trends are if the accuracy improves or not.

## 18. Document accuracy results

Can you put the graphs in the readme ujnder "## How you evaluated forecast accuracy and what the results were"

also include the forecast period / average absolute error chart.

## 19. Compare smoothing weights

can you also perform this experiment using a couple of different smoothing weights? ideally we find one that is better than 0.3

## 20. Switch smoothing weight

let's switch to 0.,8

## 21. Commit and push

commit and push to remote

## 22. Export this prompt history

export prompts.md, add to root dir, commit and push again pls
